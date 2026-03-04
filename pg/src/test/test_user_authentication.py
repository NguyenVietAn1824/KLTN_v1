from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4

from dotenv import load_dotenv
from pg import SQLDatabase
from pg.schema import City as CityModel
from pg.schema import GenderType
from pg.schema import RoleType
from pg.schema import User as UserModel
from pg.schema import UserAuthentication as UserAuthenticationModel


load_dotenv()


username = os.getenv('POSTGRES__USERNAME')
password = os.getenv('POSTGRES__PASSWORD')
database = os.getenv('POSTGRES__DB')
host = os.getenv('POSTGRES__HOST')


class TestUserAuthentication:
    """Test CRUD operations for UserAuthentication model.

    This class tests the authentication workflow, ensuring:
    - User authentication records can be created with username (email)
    - Password updates work correctly
    - Username matches user email for login consistency
    - Authentication records are properly linked to users
    """

    def __init__(self) -> None:
        self.user = username
        self.password = password
        self.host = host
        self.database = database

        self.db = SQLDatabase(self.user, self.password, self.host, self.database)

    def test_user_authentication_crud(self) -> None:
        """Test complete CRUD cycle for UserAuthentication.

        Steps:
        - Create a city and user (required dependencies)
        - Create user authentication with username = user email
        - Verify authentication can be fetched by id and username
        - Update password
        - Delete authentication and verify cleanup
        """
        # Generate IDs
        city_id = str(uuid4())
        user_id = str(uuid4())
        user_auth_id = str(uuid4())

        # Build models
        city = CityModel(id=city_id, name='Hanoi')

        user_email = 'testuser@example.com'
        user = UserModel(
            id=user_id,
            city_id=city_id,
            name='Test User',
            email=user_email,
            dob=datetime(1990, 5, 15).date(),
            phone='+84123456789',
            gender=GenderType.FEMALE,
            address='456 Test St',
            ward='Ward 2',
            avatar_url='https://example.com/avatar.jpg',
            last_active=datetime.utcnow(),
            role=RoleType.USER,
        )

        # Create authentication with username = email
        user_auth = UserAuthenticationModel(
            id=user_auth_id,
            username=user_email,  # username matches email
            password='$2b$12$hashed_password_example',  # In production, use bcrypt or similar
        )

        with self.db.get_session() as session:
            try:
                # --- INSERT ---
                print('Testing insert...')
                self.db.insert_city(session=session, model=city)
                self.db.insert_user(session=session, model=user)
                inserted_auth = self.db.insert_user_authentication(session=session, model=user_auth)

                assert inserted_auth is not None
                assert inserted_auth.username == user_email
                print(f'✓ Inserted user authentication for: {inserted_auth.username}')

                # --- READ by ID ---
                print('\nTesting get by id...')
                fetched_auth = self.db.get_user_authentication_by_id(session=session, id=user_auth_id)
                assert fetched_auth is not None
                assert fetched_auth.id == user_auth_id
                assert fetched_auth.username == user_email
                print(f'✓ Fetched authentication by ID: {fetched_auth.id}')

                # --- READ by username (email) ---
                print('\nTesting get by username...')
                auth_by_username = self.db.get_user_authentication_by_username(
                    session=session,
                    username=user_email,
                )
                assert auth_by_username is not None
                assert auth_by_username.username == user_email
                assert auth_by_username.id == user_auth_id
                print(f'✓ Fetched authentication by username: {auth_by_username.username}')

                # --- LIST ---
                print('\nTesting list authentications...')
                all_auths = self.db.get_user_authentications(session=session)
                assert all_auths is not None
                assert len(all_auths) > 0
                print(f'✓ Found {len(all_auths)} authentication record(s)')

                # --- UPDATE (change password) ---
                print('\nTesting update password...')
                user_auth.password = '$2b$12$new_hashed_password_example'
                updated_auth = self.db.update_user_authentication(session=session, model=user_auth)
                assert updated_auth is not None
                assert updated_auth.password == user_auth.password
                print(f'✓ Updated password for: {updated_auth.username}')

                # --- DELETE authentication ---
                print('\nTesting delete authentication...')
                deleted_auth = self.db.delete_user_authentication(session=session, id=user_auth_id)
                assert deleted_auth is not None
                assert deleted_auth.id == user_auth_id

                # Verify deletion
                check_deleted = self.db.get_user_authentication_by_id(session=session, id=user_auth_id)
                assert check_deleted is None
                print(f'✓ Deleted authentication for: {deleted_auth.username}')

                # --- CLEANUP dependencies ---
                print('\nCleaning up dependencies...')
                self.db.delete_user(session=session, id=user_id)
                self.db.delete_city(session=session, id=city_id)
                print('✓ Cleaned up user and city')

                print('\n✅ All UserAuthentication CRUD tests passed!')

            except Exception as e:
                print(f'\n❌ Test failed with error: {e}')
                raise

    def test_authentication_with_user_sync(self) -> None:
        """Test that username stays synced with user email.

        This test simulates:
        - Creating user and authentication
        - Verifying username matches email
        - Updating user email and authentication username together
        """
        # Generate IDs
        city_id = str(uuid4())
        user_id = str(uuid4())
        user_auth_id = str(uuid4())

        original_email = 'original@example.com'
        new_email = 'updated@example.com'

        # Build models
        city = CityModel(id=city_id, name='Da Nang')
        user = UserModel(
            id=user_id,
            city_id=city_id,
            name='Sync Test User',
            email=original_email,
            dob=datetime(1995, 3, 20).date(),
            phone='+84987654321',
            gender=GenderType.MALE,
            address='789 Sync St',
            ward='Ward 3',
            avatar_url='',
            last_active=datetime.utcnow(),
            role=RoleType.USER,
        )

        user_auth = UserAuthenticationModel(
            id=user_auth_id,
            username=original_email,
            password='$2b$12$hashed_password',
        )

        with self.db.get_session() as session:
            try:
                print('\nTesting email/username synchronization...')

                # Insert
                self.db.insert_city(session=session, model=city)
                self.db.insert_user(session=session, model=user)
                self.db.insert_user_authentication(session=session, model=user_auth)

                # Verify initial sync
                auth = self.db.get_user_authentication_by_username(session=session, username=original_email)
                fetched_user = self.db.get_user_by_id(session=session, id=user_id)
                assert auth is not None
                assert fetched_user is not None
                assert auth.username == fetched_user.email
                print(f'✓ Initial sync verified: username={auth.username}, email={fetched_user.email}')

                # Update both email and username
                user.email = new_email
                user_auth.username = new_email

                updated_user = self.db.update_user(session=session, model=user)
                updated_auth = self.db.update_user_authentication(session=session, model=user_auth)

                assert updated_user is not None
                assert updated_auth is not None
                assert updated_user.email == new_email
                assert updated_auth.username == new_email
                assert updated_user.email == updated_auth.username
                print(f'✓ Sync after update verified: username={updated_auth.username}, email={updated_user.email}')

                # Cleanup
                self.db.delete_user_authentication(session=session, id=user_auth_id)
                self.db.delete_user(session=session, id=user_id)
                self.db.delete_city(session=session, id=city_id)

                print('✅ Email/username synchronization test passed!')

            except Exception as e:
                print(f'\n❌ Sync test failed with error: {e}')
                raise


if __name__ == '__main__':
    test = TestUserAuthentication()

    # Run CRUD test
    print('=' * 60)
    print('Running UserAuthentication CRUD Test')
    print('=' * 60)
    test.test_user_authentication_crud()

    # Run synchronization test
    print('\n' + '=' * 60)
    print('Running Email/Username Synchronization Test')
    print('=' * 60)
    test.test_authentication_with_user_sync()

    print('\n' + '=' * 60)
    print('🎉 All tests completed successfully!')
    print('=' * 60)
