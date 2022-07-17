"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()
        # User.query.delete()
        # Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 901

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_unauthorized_add_msg(self):
        """Don't allow adding messages without logging in"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            content = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized", content)

    def test_unauthorized_del_msg(self):
        """No deleting messages when not logged in"""

        test_msg = Message(
            text = "Test test test test hi hi",
            user_id = self.testuser.id,
            )
        
        db.session.add(test_msg)
        db.session.commit()

        with self.client as c:

                resp = c.post(f"/messages/{test_msg.id}/delete", follow_redirects=True)
                content = resp.get_data(as_text=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", content)


    def test_deleting_other_user_msg(self):
        """"No deleting other users messages"""

        other_user = User.signup(username="hackyuser", email="hackyuser@test.com", password="password", image_url=None)
        other_user.id = 555

        test_msg = Message(
            id=222,
            text="Test test test test hi hi",
            user_id=self.testuser.id,
            )
        
        db.session.add(test_msg)
        db.session.add(other_user)

        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 555

            resp = c.post("/messages/222/delete", follow_redirects=True)
            content = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", content)

                

