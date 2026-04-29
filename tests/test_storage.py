import os, tempfile, pytest
from storage.database import Database
from storage.migrations import run_migrations

@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    run_migrations(path)
    yield Database(path)
    os.unlink(path)

def test_save_and_get_thread(db):
    tid = db.save_thread("Bitcoin ETF", "educational", ["tweet1", "tweet2"])
    thread = db.get_thread(tid)
    assert thread["topic"] == "Bitcoin ETF"
    assert thread["tweets"] == ["tweet1", "tweet2"]
    assert thread["status"] == "draft"

def test_topic_dedup(db):
    db.save_topic("bitcoin etf approval")
    assert db.is_topic_used("Bitcoin ETF Approval") is True
    assert db.is_topic_used("ethereum merge") is False

def test_mark_posted(db):
    tid = db.save_thread("Test", "hot_take", ["t1"])
    db.mark_posted(tid, "1234567890")
    thread = db.get_thread(tid)
    assert thread["status"] == "posted"
