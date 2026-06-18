"""
Golden test cases for ReviewBot evaluation — 10 PRs covering a range of scenarios.
All PRs are from public repos chosen to exercise specific dimensions.
"""

TEST_CASES = [
    {
        "id": "hardcoded_secret",
        "description": "PR adding a literal API secret directly in source code",
        # mpirnat/lets-be-bad-guys PR#7 — adds bad.py containing: API_SECRET = "XXX"
        "pr_url": "https://github.com/mpirnat/lets-be-bad-guys/pull/7",
        "expected_findings": [
            {
                "dimension": "security",
                "keywords": ["hardcoded", "secret", "credential", "api", "password"],
                "min_severity": "high",
            }
        ],
        "score_bounds": {
            "security": {"max": 50},
            "overall": {"max": 60},
        },
    },
    {
        "id": "sql_injection",
        "description": "PR introducing SQL injection via f-string and XSS via raw HTML rendering",
        # anxolerd/dvpwa PR#59 — adds: q = f"SELECT ... WHERE name ILIKE '%{search_term}%'"
        # plus unsafe HTML injection via _process_review_text
        "pr_url": "https://github.com/anxolerd/dvpwa/pull/59",
        "expected_findings": [
            {
                "dimension": "security",
                "keywords": ["sql", "injection", "f-string", "format", "unsanitized", "xss", "html"],
                "min_severity": "high",
            }
        ],
        "score_bounds": {
            "security": {"max": 45},
            "overall": {"max": 60},
        },
    },
    {
        "id": "reflected_xss",
        "description": "PR adding a Flask route with reflected XSS: return f'<h1>Hello {name}</h1>'",
        # anxolerd/dvpwa PR#44 — adds greet() route that renders user input directly into HTML
        "pr_url": "https://github.com/anxolerd/dvpwa/pull/44",
        "expected_findings": [
            {
                "dimension": "security",
                "keywords": ["xss", "cross-site", "reflected", "html", "escape", "sanitize", "inject"],
                "min_severity": "high",
            }
        ],
        "score_bounds": {
            "security": {"max": 45},
            "overall": {"max": 60},
        },
    },
    {
        "id": "no_tests",
        "description": "PR adding new Python endpoint and deployment logic with zero test file changes",
        # erev0s/VAmPI PR#73 — adds deployment_test() endpoint, start_production.py — no tests
        "pr_url": "https://github.com/erev0s/VAmPI/pull/73",
        "expected_findings": [
            {
                "dimension": "testing",
                "keywords": ["test", "coverage", "missing", "untested", "no test"],
                "min_severity": "medium",
            }
        ],
        "score_bounds": {
            "testing": {"max": 60},
        },
    },
    {
        "id": "well_tested",
        "description": "PR adding Tags CRUD REST API with 23 tests and claimed 100% coverage",
        # miguelgrinberg/flasky PR#576 — new tags.py endpoint + test_tags_api.py (269 lines of tests)
        "pr_url": "https://github.com/miguelgrinberg/flasky/pull/576",
        "expected_findings": [],
        "score_bounds": {
            "testing": {"min": 70},
            "overall": {"min": 65},
        },
    },
    {
        "id": "partial_coverage",
        "description": "PR adding analytics/export service with tests covering only some of the new logic",
        # miguelgrinberg/flasky PR#575 — adds export_manager.py (+149) + post_service.py (+21)
        # with tests/test_analytics_export.py (+108) — tests exist but don't cover everything
        "pr_url": "https://github.com/miguelgrinberg/flasky/pull/575",
        "expected_findings": [],
        "score_bounds": {
            "testing": {"min": 40, "max": 90},
            "overall": {"min": 20},
        },
    },
    {
        "id": "clean_pr",
        "description": "Tiny docs-only fix (2 lines) in a mature library — should score high everywhere",
        # psf/requests PR#519 — 'little correction of curl in docs' — +2/-2 in 1 docs file
        "pr_url": "https://github.com/psf/requests/pull/519",
        "expected_findings": [],
        "score_bounds": {
            "overall": {"min": 70},
            "security": {"min": 75},
            "testing": {"min": 75},
        },
    },
    {
        "id": "dependency_update",
        "description": "PR adding a single dependency to requirements.txt — no code logic changed",
        # NetSPI/django.nV PR#75 — adds 'immunio' to requirements.txt (+1/-0 files:1)
        "pr_url": "https://github.com/NetSPI/django.nV/pull/75",
        "expected_findings": [],
        "score_bounds": {
            "testing": {"min": 75},
            "overall": {"min": 30},
        },
    },
    {
        "id": "complex_with_tests",
        "description": "Django model refactor with new business logic and corresponding tests",
        # archlinux/archweb PR#711 — adds flag_peers() method + get_associated_packages refactor
        # + 86 lines of tests in test_flag_packages.py
        "pr_url": "https://github.com/archlinux/archweb/pull/711",
        "expected_findings": [],
        "score_bounds": {
            "testing": {"min": 60},
            "overall": {"min": 55},
        },
    },
    {
        "id": "auth_bypass",
        "description": "PR exposing authorization bypass — reads user from request after auth check using different user",
        # NetSPI/django.nV PR#86 — adds comments documenting auth bypass and path traversal sinks
        # in manage_projects and upload views; the vulnerable logic is present in + lines
        "pr_url": "https://github.com/NetSPI/django.nV/pull/86",
        "expected_findings": [
            {
                "dimension": "security",
                "keywords": ["authorization", "auth", "bypass", "path traversal", "injection", "traversal", "request"],
                "min_severity": "medium",
            }
        ],
        "score_bounds": {
            "security": {"max": 65},
        },
    },
]

# PRs run twice to measure score drift (target: ≤10 points variance per dimension)
CONSISTENCY_TEST_PRS = [
    "https://github.com/anxolerd/dvpwa/pull/59",
    "https://github.com/psf/requests/pull/519",
]
