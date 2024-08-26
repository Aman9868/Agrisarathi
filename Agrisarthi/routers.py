class MasterSlaveRouter:
    def db_for_read(self, model, **hints):
        """Directs read operations to the slave database."""
        return 'slave'

    def db_for_write(self, model, **hints):
        """Directs write operations to the master database."""
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allows relations between objects in the same database."""
        return obj1._state.db in ('default', 'slave') and obj2._state.db in ('default', 'slave')

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensures that all models are migrated to the master database."""
        return db == 'default'
