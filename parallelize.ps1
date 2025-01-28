<#
.SYNOPSIS
    Generate commands based on dynamic ranges and execute them in parallel.

.DESCRIPTION
    This script generates commands based on dynamic ranges and executes them in parallel.

.PARAMETER RangeSize
    The size of each range. Defaults to 100 if not specified.

.PARAMETER MaxParallel
    The maximum number of processes allowed to run concurrently. Defaults to 6.

.PARAMETER DelayBetweenJobs
    The number of seconds to delay between starting new jobs. Defaults to 2 seconds.

.PARAMETER MinFactor
    The minimum factor to use when calculating the range size. Defaults to 5.

.PARAMETER UpperLimit
    The maximum upper limit for the ranges. This parameter is required.

.PARAMETER Domain
    The domain for the URL and output file name. This parameter is required, with domain parts reversed, and 'www' removed if present.

.EXAMPLE
    .\parallelize.ps1 -UpperLimit 999 -Domain "www.domain.com"
    Runs with an upper limit of 999 and a default range size of 100, using the domain reversed in the file name with 'www' removed.

.EXAMPLE
    .\parallelize.ps1 -UpperLimit 1000 -RangeSize 50 -Domain "subdomain.domain.com"
    Runs with an upper limit of 1000 and a range size of 50, using the domain reversed in the file name.
#>

param (
    [Parameter(Mandatory = $false)]
    [int]$RangeSize = 100,      # Optional range size, defaults to 100

    [Parameter(Mandatory = $false)]
    [int]$MaxParallel = 6,      # Optional maximum parallel processes (default to 4)

    [Parameter(Mandatory = $false)]
    [int]$DelayBetweenJobs = 2, # Delay between starting each job (in seconds)

    [Parameter(Mandatory = $false)]
    [int]$MinFactor = 5,        # Minimum factor size (defaults to 5)

    [Parameter(Mandatory = $true)]
    [string]$Domain,            # Required domain

    [Parameter(Mandatory = $true)]
    [int]$UpperLimit            # Required upper limit
)

# Function to find the valid factor based on the desired range (7% to 13%)
function Get-ValidFactor {
    param (
        [int]$UpperLimit,
        [int]$MinFactorPercentage = 7,   # Minimum percentage (7% of UpperLimit)
        [int]$MaxFactorPercentage = 13,   # Maximum percentage (13% of UpperLimit)
        [int]$MaxFactor = 250            # Cap the maximum factor at 250
    )

    # Calculate the minimum and maximum acceptable range size
    $minFactor = [Math]::Floor($UpperLimit * ($MinFactorPercentage / 100))
    $maxFactor = [Math]::Floor($UpperLimit * ($MaxFactorPercentage / 100))

    # Ensure that no factor exceeds the maximum allowed range
    $maxFactor = [Math]::Min($maxFactor, $MaxFactor)

    # Loop through factors from 1 up to UpperLimit
    $validFactors = @()

    # Find all factors of the UpperLimit
    for ($i = $MinFactor; $i -le $UpperLimit; $i++) {
        if ($UpperLimit % $i -eq 0) {
            # Check if the factor is within the desired percentage range
            if ($i -ge $minFactor -and $i -le $maxFactor) {
                $validFactors += $i
            }
        }
    }

    # Return the largest valid factor in the list (if any), otherwise return 10% of UpperLimit as default
    if ($validFactors.Count -gt 0) {
        # Return the largest valid factor
        $RangeSize = $validFactors | Sort-Object -Descending | Select-Object -First 1
    } else {
        # Default to ~10% of the UpperLimit if no valid factor found
        $RangeSize = [Math]::Floor($UpperLimit * 0.10)
    }

    return $RangeSize
}

# Determine RangeSize dynamically if not provided
if (-not $PSBoundParameters.ContainsKey("RangeSize")) {
    $RangeSize = Get-ValidFactor -UpperLimit $UpperLimit
    Write-Host "Using Computed RangeSize: $RangeSize"
}

# Function to reverse the domain parts and remove 'www' if present
function Get-ReversedDomain {
    param ($Domain)

    # Check if 'www' is a subdomain and remove it if present
    $DomainParts = $Domain.Split('.')
    
    if ($DomainParts[0] -eq "www") {
        # Remove 'www' from the domain
        $DomainParts = $DomainParts[1..($DomainParts.Length - 1)]
    }
    
    # Reverse the domain parts and join them
    $ReversedDomain = [String]::Join('.', $DomainParts[-1..0])  # Reverse the array and join
    return $ReversedDomain
}

# Reverse the domain (and remove 'www' if present)
$ReversedDomain = Get-ReversedDomain -Domain $Domain
# Get the current date in the required format (yyyy-MM-dd)
$CurrentDate = Get-Date -Format "yyyy-MM-dd"

# Generate the ranges
$ranges = 0..($UpperLimit / $RangeSize) | ForEach-Object {
    $Lower = $_ * $RangeSize
    $Upper = [Math]::Min($Lower + $RangeSize - 1, $UpperLimit - 1)
    @{ Lower = $Lower; Upper = $Upper }
}

try {
    # Manage job throttling
    $jobs = @()

    # Run commands in parallel
    foreach ($range in $ranges) {
        $Lower = $range["Lower"]
        $Upper = $range["Upper"]

        # Define the output file and the command
        $OutputFile = "${ReversedDomain}__${CurrentDate}__" + ($Lower + 1) + "-" + ($Upper + 1) + ".epub"
        $Command = "blog2epub -o '$OutputFile' -q 100 'https://$Domain/' -s ${Lower} -l ${RangeSize} -e blogger"
        
        Write-Host "Queuing: $Command"

        # Start a new job
        $job = Start-Job -ScriptBlock {
            param ($OutputFile, $Command)
            Write-Host "Executing: $Command"
            Invoke-Expression $Command
        } -ArgumentList $OutputFile, $Command
        $jobs += $job

        # Check if the number of running jobs exceeds the limit
        while ($jobs.Count -ge $MaxParallel) {
            # Wait for any job to complete
            $completedJobs = $jobs | Where-Object { $_.State -ne 'Running' }
            $completedJobs | ForEach-Object {
                $_ | Receive-Job  # Output job results
                Remove-Job $_     # Clean up the job
            }
            $jobs = $jobs | Where-Object { $_.State -eq 'Running' }
            Start-Sleep -Seconds 1
        }

        # Add delay before starting the next job
        Start-Sleep -Seconds $DelayBetweenJobs
    }

    # Wait for any remaining jobs to complete
    foreach ($job in $jobs) {
        $job | Wait-Job | Receive-Job
        Remove-Job $job
    }

    Write-Host "All tasks complete."
} catch {
    Write-Host "An error occurred: $_"
} finally {
     # Clean up jobs if Ctrl+C (keyboard interrupt) or any other break happens
    Write-Host "Cleaning up running jobs..."
    
    # Terminate any jobs that are still running
    foreach ($job in $jobs) {
        if ($job.State -eq 'Running') {
            Stop-Job $job
            Write-Host "Job stopped: $job"
        }
        Remove-Job $job
    }

    Write-Host "All tasks complete or terminated."
}
