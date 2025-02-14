import re


def translate_month(date: str, language: str) -> str:
    date = date.lower()
    if language == "pl":
        for dn in ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]:
            date = date.replace(dn, "")
        date = date.strip(",")
        date = date.strip()
        replace_dict = {
            "stycznia": "january",
            "lutego": "february",
            "marca": "march",
            "kwietnia": "april",
            "maja": "may",
            "czerwca": "june",
            "lipca": "july",
            "sierpnia": "august",
            "września": "september",
            "października": "october",
            "listopada": "november",
            "grudnia": "december",
        }
        replace_dict_short = {}
        for key, val in replace_dict.items():
            date = date.replace(key, val)
            replace_dict_short[f" {key[0:3]} "] = f" {val} "
        for key, val in replace_dict_short.items():
            date = date.replace(key, val)
    if language == "ru":
        for dn in ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]:
            date = date.replace(dn, "")
        date = date.strip(",")
        replace_dict = {
            "января": "january",
            "февраля": "february",
            "марта": "march",
            "апреля": "april",
            "мая": "may",
            "июня": "june",
            "июля": "july",
            "августа": "august",
            "сентября": "september",
            "октября": "october",
            "ноября": "november",
            "декабря": "december",
        }
        for key, val in replace_dict.items():
            date = date.replace(key, val)
        date = re.sub(r"\sг.$", "", date)
    if language == "de":
        replace_dict = {
            "januar": "january",
            "februar": "february",
            "märz": "march",
            "mai": "may",
            "juni": "june",
            "juli": "july",
            "oktober": "october",
            "dezember": "december",
        }
        for key, val in replace_dict.items():
            date = date.replace(key, val)
    return date
