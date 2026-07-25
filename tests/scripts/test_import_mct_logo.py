from scripts.import_mct_logo import git_blob_sha


def test_git_blob_sha_matches_git_object_format() -> None:
    assert git_blob_sha(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"
