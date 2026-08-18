
class RBAC:
    def __init__(self):
        self.roles = {
            "Administrator": ["read", "write", "delete", "manage_users", "train_model", "deploy_model"],
            "Developer": ["read", "write", "train_model", "deploy_model"],
            "Researcher": ["read", "train_model"],
            "Standard User": ["read", "infer"],
            "Guest": ["read"]
        }

    def has_permission(self, role, action):
        return action in self.roles.get(role, [])
