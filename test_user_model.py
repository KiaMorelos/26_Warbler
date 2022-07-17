"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for Users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()
        #Was this placed here to be confusing. it's not used anywhere in the solution?
        # User.query.delete()
        # Message.query.delete()
        # Follows.query.delete()

        user_one = User.signup("testuser", "testu@gmail.com", "password", None)
        user_two = User.signup("testuser2", "testu@yahoo.com", "password", None)
       
        user_one.id = 777
        user_two.id = 999

        db.session.add(user_one)
        db.session.add(user_two)

        db.session.commit()

        # user1 = User.query.get(777)
        # user2 = User.query.get(999)

        self.user1 = user_one
        self.user2 = user_two

        self.client = app.test_client()
    
    def tearDown(self):
         db.session.rollback()
         
  
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser4",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_following_followers(self):
        """Test following and followers"""
    
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user2.followers), 1)

    def test_is_followed_by(self):
        """Test is followed by"""

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))


    def test_is_following(self):
        """Test is following"""

        self.user2.following.append(self.user1)
        db.session.commit()

        self.assertFalse(self.user2.is_followed_by(self.user1))
        self.assertTrue(self.user1.is_followed_by(self.user2))

    def test_create_user(self):
        """Create user via signup"""
        
        new_user = User.signup("FakeName", "fakeEmail@fake.com", "password", None)
        new_user.id = 1001

        db.session.add(new_user)
        db.session.commit()

        user = User.query.get(1001)

        self.assertIsNotNone(user)
        self.assertIsInstance(user, User, msg="Is instance of User class")
        self.assertEqual(user.username, "FakeName")
        self.assertEqual(user.email, "fakeEmail@fake.com")

    def test_not_unique_user(self):
        """Test using duplicate username"""
        
        new_user = User.signup("testuser", "fakeEmail@fake.com", "password", None)
        db.session.add(new_user)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_non_nullable_user(self):
        """Test that non-nullable field being blank fails"""
        new_user = User.signup(None, "fakeEmail@fake.com", "password", None)
        db.session.add(new_user)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_authentication(self):
        """Test Authentication"""

        user = User.authenticate(self.user1.username, "password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1.id)

    def test_invalid_username(self):
        """Test invalid username fails"""
        
        user = User.authenticate("wrongName", "password")
        self.assertFalse(user)

    def test_wrong_password(self):
        """Wrong Password should fail"""
    
        user = User.authenticate(self.user1.username, "wroooooong")
        self.assertFalse(user)




        
