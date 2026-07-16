import unittest

class RollbackHandlerTests(unittest.TestCase):
    def test_handler_imports(self):
        from agent.jobs.rollback import handle_rollback_update
        self.assertTrue(callable(handle_rollback_update))

if __name__ == "__main__":
    unittest.main()
