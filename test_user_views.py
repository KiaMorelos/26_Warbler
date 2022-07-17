"""User View tests."""

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


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        # User.query.delete()
        # Message.query.delete()

        self.client = app.test_client()

        user_one = User.signup("testuser", "testu@gmail.com", "password", None)
        user_two = User.signup("otherPerson", "testu@yahoo.com", "password", None)
       
        user_one.id = 777
        user_two.id = 999


        db.session.add(user_one)
        db.session.add(user_two)

        db.session.commit()

        self.user1 = user_one
        self.user2 = user_two


    def tearDown(self):
        db.session.rollback()


    def test_view_followers(self):
        """Check followers view"""
        self.user1.following.append(self.user2)
        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id

            resp = c.get("/users/999/followers")

            self.assertEqual(resp.status_code, 200)
            content = resp.get_data(as_text=True)
            self.assertIn("@testuser", content)

    def test_view_following(self):
        """Check followers view"""
        self.user1.following.append(self.user2)
        db.session.commit()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.get("/users/777/following")

            self.assertEqual(resp.status_code, 200)
            content = resp.get_data(as_text=True)
            self.assertIn("@otherPerson", content)

    def test_not_authorized_following(self):
        """Don't allow viewing of following page when not logged in"""

        self.user1.following.append(self.user2)
        db.session.commit()

        with self.client as c:

            resp = c.get("/users/777/following", follow_redirects=True)
            content = resp.get_data(as_text=True)
            self.assertNotIn("@otherPerson", content)
            self.assertIn("Access unauthorized", content)
            
    def test_not_authorized_followers(self):
        """Don't allow viewing of follower page when not logged in"""

        self.user1.following.append(self.user2)
        db.session.commit()

        with self.client as c:

            resp = c.get("/users/999/followers", follow_redirects=True)
            content = resp.get_data(as_text=True)
            self.assertNotIn("@testuser", content)
            self.assertIn("Access unauthorized", content)

    def test_add_messages_unauthorized(self):
        """No access to new message form when not logged in"""
        
        with self.client as c:

            resp = c.get("/messages/new", follow_redirects=True)
            content = resp.get_data(as_text=True)
            self.assertNotIn("New Message", content)
            self.assertIn("Access unauthorized", content)

    def test_add_messages_route(self):
        """Access to new message form when logged in"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id

            resp = c.get("/messages/new", follow_redirects=True)
            content = resp.get_data(as_text=True)
            self.assertIn("Add my message!", content)

       