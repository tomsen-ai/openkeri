def isPalindrome(s):
    cleaned = "".join(ch.lower() for ch in s if ch.isalpha())
    return cleaned == cleaned[::-1]
