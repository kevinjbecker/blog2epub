<#
.SYNOPSIS
    Generate commands based on dynamic ranges and execute them in parallel.

.DESCRIPTION
    This script generates commands based on dynamic ranges and executes them in parallel.

.PARAMETER UpperLimit
    The maximum upper limit for the ranges. This parameter is required.

.PARAMETER RangeSize
    The size of each range. Defaults to 100 if not specified.

.PARAMETER Domain
    The domain for the URL and output file name. This parameter is required, with domain parts reversed, and 'www' removed if present.

.PARAMETER MaxParallel
    The maximum number of processes allowed to run concurrently. Defaults to 6.

.PARAMETER DelayBetweenJobs
    The number of seconds to delay between starting new jobs. Defaults to 2 seconds.

.PARAMETER MinFactor
    The minimum factor to use when calculating the range size. Defaults to 5.

.EXAMPLE
    .\parallelize.ps1 -UpperLimit 999 -Domain "www.domain.com"
    Runs with an upper limit of 999 and a default range size of 100, using the domain reversed in the file name with 'www' removed.

.EXAMPLE
    .\parallelize.ps1 -UpperLimit 1000 -RangeSize 50 -Domain "subdomain.domain.com"
    Runs with an upper limit of 1000 and a range size of 50, using the domain reversed in the file name.
#>

param (
    [Parameter(Mandatory = $true)]
    [int]$UpperLimit,        # Required upper limit

    [Parameter(Mandatory = $false)]
    [int]$RangeSize = 100,   # Optional range size, defaults to 100

    [Parameter(Mandatory = $true)]
    [string]$Domain          # Required domain

    [Parameter(Mandatory = $false)]
    [int]$MaxParallel = 6    # Optional maximum parallel processes (default to 4)

    [Parameter(Mandatory = $false)]
    [int]$DelayBetweenJobs = 2 # Delay between starting each job (in seconds)

    [Parameter(Mandatory = $false)]
    [int]$MinFactor = 5      # Minimum factor size (defaults to 5)
)

# Function to calculate the smallest factor ≤ 100
function Get-SmallestFactor {
    param (
        [int]$Number,         # The number to find a factor for
        [int]$MinFactor = 5,  # The minimum factor allowed
        [int]$MaxFactor = 100 # The maximum factor allowed
    )

    for ($i = $MinFactor; $i -le $MaxFactor; $i++) {
        if ($Number % $i -eq 0) {
            return $i
        }
    }

    # If no factor is found, return the maximum allowed factor
    return $MaxFactor
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

# Determine RangeSize dynamically if not provided
if (-not $PSBoundParameters.ContainsKey("RangeSize")) {
    $RangeSize = Get-SmallestFactor -Number $UpperLimit
    Write-Host "Using Computed RangeSize: $RangeSize"
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
