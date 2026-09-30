from __future__ import annotations


_HELPLINES = {
    "united states": {
        "name": "988 Suicide & Crisis Lifeline",
        "number": "988",
        "method": "Call or text",
        "url": "https://988lifeline.org/",
    },
    "canada": {
        "name": "9-8-8 Suicide Crisis Helpline",
        "number": "988",
        "method": "Call or text",
        "url": "https://988.ca/",
    },
    "united kingdom": {
        "name": "Samaritans",
        "number": "116 123",
        "method": "Call",
        "url": "https://www.samaritans.org/how-we-can-help/contact-samaritan/",
    },
    "ireland": {
        "name": "Samaritans Ireland",
        "number": "116 123",
        "method": "Call",
        "url": "https://www.samaritans.org/ireland/how-we-can-help/contact-samaritan/",
    },
    "australia": {
        "name": "Lifeline",
        "number": "13 11 14",
        "method": "Call",
        "url": "https://www.lifeline.org.au/",
    },
    "india": {
        "name": "Tele-MANAS",
        "number": "14416",
        "method": "Call",
        "url": "https://telemanas.mohfw.gov.in/",
    },
}

_ALIASES = {
    "us": "united states",
    "usa": "united states",
    "united states of america": "united states",
    "uk": "united kingdom",
    "great britain": "united kingdom",
    "republic of ireland": "ireland",
}


def normalize_country(country: str) -> str:
    value = " ".join(country.strip().casefold().split())
    canonical = _ALIASES.get(value, value)
    names = {
        "united states": "United States",
        "canada": "Canada",
        "united kingdom": "United Kingdom",
        "ireland": "Ireland",
        "australia": "Australia",
        "india": "India",
    }
    return names.get(canonical, country.strip())


def helpline_for_country(country: str) -> dict[str, str | bool]:
    normalized = " ".join(country.strip().casefold().split())
    canonical = _ALIASES.get(normalized, normalized)
    helpline = _HELPLINES.get(canonical)
    if helpline:
        return {"country": normalize_country(country), **helpline, "verified": True}
    return {
        "country": country,
        "name": "Find a verified local helpline",
        "number": "",
        "method": "",
        "url": "https://findahelpline.com/",
        "verified": False,
    }