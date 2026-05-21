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
