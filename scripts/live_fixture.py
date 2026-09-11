"""Controlled test-only actor; never approves PRs or bypasses branch rules."""
import base64
import json
import os
import subprocess
import tempfile
from urllib.parse import quote


REPO = "whm-cell/github-team-flow-e2e-20260911-022206"
assert os.environ["GITHUB_REPOSITORY"] == REPO


def cli(*args):
    return subprocess.check_output(["gh", *args], text=True).strip()


def api(path, method="GET", data=None):
    args = ["api", f"repos/{REPO}/{path}", "--method", method]
    if data is None:
        raw = cli(*args)
    else:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            json.dump(data, f)
            f.flush()
            raw = cli(*args, "--input", f.name)
    return json.loads(raw) if raw else None


def tip(branch):
    return api("git/ref/heads/" + quote(branch, safe=""))["object"]["sha"]


def content(path, branch):
    item = api("contents/" + path + "?ref=" + quote(branch, safe=""))
    return base64.b64decode(item["content"]).decode()


def commit_files(branch, changes, message):
    parent = tip(branch)
    tree = api("git/commits/" + parent)["tree"]["sha"]
    entries = []
    for path, value in changes.items():
        entry = {"path": path, "mode": "100644", "type": "blob"}
        entry["sha" if value is None else "content"] = value
        entries.append(entry)
    tree = api("git/trees", "POST", {"base_tree": tree, "tree": entries})["sha"]
    commit = api("git/commits", "POST", {"message": message, "tree": tree, "parents": [parent]})["sha"]
    if tip(branch) != parent:
        raise RuntimeError("Fixture branch changed during preparation")
    api("git/refs/heads/" + quote(branch, safe=""), "PATCH", {"sha": commit, "force": False})
    return commit


def find_pr(branch, state="open"):
    items = api("pulls?state=" + state + "&head=" + quote("whm-cell:" + branch, safe="") + "&base=main&per_page=100")
    return [p for p in items if p["head"]["repo"]["full_name"] == REPO]


def ensure_pr(branch, title, depends):
    existing = find_pr(branch)
    if len(existing) > 1:
        raise RuntimeError("Ambiguous fixture PR")
    if existing:
        item = existing[0]
        if item["user"]["type"] != "Bot":
            raise RuntimeError("Close the human-authored test PR before creating the bot fixture")
        return item
    body = ("Synthetic GitHub API integration test. The Actions bot authors this PR so the "
            "owner account can exercise real review endpoints. This is controlled technical "
            "coverage, not independent human business review.\n\n"
            "Enrollment and classroom modules use actual Python code and integration tests. "
            "Intentionally defective or missing upstream contracts must block merging.\n\n"
            "<!-- team-flow: " + json.dumps({"depends_on": depends}) + " -->\n")
    return api("pulls", "POST", {"title": title, "head": branch, "base": "main", "body": body})


mode = os.environ["FIXTURE_MODE"]
if mode in ("bad-contract", "good-contract"):
    branch = "test/contract-api"
    source = content("enrollment.py", branch)
    good = "return self.is_enrolled(course_id, student_id)"
    bad = "return True  # intentional live-test defect"
    if mode == "bad-contract":
        if good not in source:
            raise RuntimeError("Expected reviewed initial contract source")
        source = source.replace(good, bad)
    else:
        if bad not in source:
            raise RuntimeError("Expected intentional defect to repair")
        source = source.replace(bad, good)
    tests = '''import unittest
from enrollment import EnrollmentRegistry

class AccessContractTests(unittest.TestCase):
    def test_access_requires_paid_enrollment_in_same_course(self):
        registry = EnrollmentRegistry()
        self.assertFalse(registry.has_access("course", "student"))
        registry.enroll("other-course", "student")
        self.assertFalse(registry.has_access("course", "student"))
        registry.enroll("course", "student")
        self.assertTrue(registry.has_access("course", "student"))
'''
    head = commit_files(branch, {"enrollment.py": source, "tests/test_access_contract.py": tests},
                        "test: " + mode + " for live required-check verification")
    pr = ensure_pr(branch, "test: enrollment access contract (controlled bot fixture)", [])
elif mode in ("adopt-client", "sync-client"):
    branch = "test/classroom-client"
    if mode == "adopt-client":
        tests = '''import unittest
from enrollment import EnrollmentRegistry
from classroom import Classroom

class ClassroomClientContractTests(unittest.TestCase):
    def test_client_obeys_access_contract_denial(self):
        class DeniedRegistry(EnrollmentRegistry):
            def has_access(self, course_id, student_id):
                return False
        registry = DeniedRegistry()
        registry.enroll("course", "student")
        room = Classroom("course", "teacher", registry)
        with self.assertRaises(PermissionError):
            room.join("student")
'''
        head = commit_files(branch, {"tests/test_client_contract.py": tests},
                            "test: verify classroom consumes the access contract")
    else:
        api("merges", "POST", {"base": branch, "head": tip("main"),
            "commit_message": "test: integrate the verified latest main into classroom client"})
        head = tip(branch)
    candidates = [p for p in find_pr("test/contract-api", "all") if p["user"]["type"] == "Bot"]
    if len(candidates) != 1:
        raise RuntimeError("Need one bot-authored contract PR dependency")
    pr = ensure_pr(branch, "test: classroom client depends on enrollment contract", [candidates[0]["number"]])
elif mode == "adopt-revert":
    branch = "test/revert-classroom"
    head = commit_files(branch, {"test-revert-receipt.md": "Synthetic classroom consumer revert; enrollment contract is retained.\n"},
                        "test: record controlled revert candidate")
    pr = ensure_pr(branch, "test: revert classroom client through protected PR", [])
else:
    raise RuntimeError("Unknown fixture mode")
print(json.dumps({"mode": mode, "branch": branch, "head": head, "pr": pr["number"],
                  "url": pr["html_url"], "author": pr["user"]["login"]}))
