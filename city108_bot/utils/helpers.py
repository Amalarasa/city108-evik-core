import re

# Извлекает имя пользователя из свободной формы ввода
# Например: "Меня зовут Алекс", "Я — Мария"
def extract_name(text):
    patterns = [
        r"(?:меня зовут|мои звать|её|моя имя|мои названи|меня)[\s:–]*([А-Яа-яA-Za-z\-].+)"
        r"^([А-Яа-яA-Za-z\-]{3,})$"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().capitalize()
    return text.strip().split()[0].capitalize()
