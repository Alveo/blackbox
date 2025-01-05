class TreeNode(object):
    
    def __init__(self, path, name):
        self.path = path
        self.name = name
        
    def __str__(self):
        return self.name