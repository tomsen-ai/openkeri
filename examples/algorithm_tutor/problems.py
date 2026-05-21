from openkeri.evidence import ProblemTestCase, ProblemTestSuite
from openkeri.schemas import Problem


def build_leetcode_3_problem() -> Problem:
    return Problem(
        id="leetcode_3",
        title="Longest Substring Without Repeating Characters",
        description=(
            "Given a string s, return the length of the longest substring without "
            "repeating characters."
        ),
        target_concepts=["sliding_window", "hash_map"],
        difficulty="medium",
    )


def build_leetcode_3_test_suite() -> ProblemTestSuite:
    return ProblemTestSuite(
        problem_id="leetcode_3",
        entrypoint="lengthOfLongestSubstring",
        test_cases=[
            ProblemTestCase(input="abcabcbb", expected=3),
            ProblemTestCase(input="bbbbb", expected=1),
            ProblemTestCase(input="pwwkew", expected=3),
            ProblemTestCase(input="abba", expected=2),
        ],
    )


def build_valid_palindrome_problem() -> Problem:
    return Problem(
        id="valid_palindrome",
        title="Valid Palindrome",
        description=(
            "Given a string s, return true if it is a palindrome after converting "
            "uppercase letters into lowercase letters and removing non-alphanumeric "
            "characters."
        ),
        target_concepts=["two_pointers", "string"],
        difficulty="easy",
    )


def build_valid_palindrome_test_suite() -> ProblemTestSuite:
    return ProblemTestSuite(
        problem_id="valid_palindrome",
        entrypoint="isPalindrome",
        test_cases=[
            ProblemTestCase(input="A man, a plan, a canal: Panama", expected=True),
            ProblemTestCase(input="race a car", expected=False),
            ProblemTestCase(input=" ", expected=True),
            ProblemTestCase(input="0P", expected=False),
        ],
    )
