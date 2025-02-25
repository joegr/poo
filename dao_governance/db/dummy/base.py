"""
Dummy database backend for Django.
This is used during collectstatic in Docker build to avoid requiring a real database connection.
"""

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.dummy.features import DummyDatabaseFeatures


class DatabaseOperations(BaseDatabaseOperations):
    """Dummy implementation of database operations."""
    
    def quote_name(self, name):
        """Return the quoted name."""
        return name


class DatabaseClient(BaseDatabaseClient):
    """Dummy database client."""
    
    executable_name = 'dummy'


class DatabaseCreation(BaseDatabaseCreation):
    """Dummy database creation."""
    
    def create_test_db(self, *args, **kwargs):
        """Create a test database."""
        return "dummy_test_db"
    
    def destroy_test_db(self, *args, **kwargs):
        """Destroy a test database."""
        pass


class DatabaseIntrospection(BaseDatabaseIntrospection):
    """Dummy database introspection."""
    
    def get_table_list(self, cursor):
        """Return an empty list of tables."""
        return []


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    """Dummy schema editor."""
    
    def __enter__(self):
        """Enter the schema editor."""
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the schema editor."""
        pass


class DatabaseWrapper(BaseDatabaseWrapper):
    """Dummy database wrapper that doesn't require a real database connection."""
    
    vendor = 'dummy'
    display_name = 'Dummy'
    
    # Override the base attributes
    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DummyDatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations
    
    # Dummy attributes
    _dummy_cursor = None
    
    def get_connection_params(self):
        """Return dummy connection parameters."""
        return {}
    
    def get_new_connection(self, conn_params):
        """Return a dummy connection."""
        return "dummy_connection"
    
    def init_connection_state(self):
        """Initialize the connection state."""
        pass
    
    def create_cursor(self, name=None):
        """Return a dummy cursor."""
        return "dummy_cursor"
    
    def schema_editor(self, *args, **kwargs):
        """Return a dummy schema editor."""
        return DatabaseSchemaEditor(self, *args, **kwargs)
    
    def is_usable(self):
        """Always return True."""
        return True 