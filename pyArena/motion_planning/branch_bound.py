import numpy as np
from graph import Graph

class BranchAndBound:
    def __init__(self, graph):
        self.graph = graph

    def compute_path(self, id_start, id_goal, budget, path):
        is_leaf = True
        for index in range(0,len(self.graph.vertices[id_start].children)):
            path_new = path + [self.graph.vertices[id_start].edge[index]]
            vertice_new = self.graph.vertices[id_start].children[index]
            budget -= self.graph.vertices[id_start].cost[index]

# Graph
mx = 3
my = 3
neighborhood = np.array([[0,0],[-1,0],[0,-1],[1,0],[0,1]])

branch_bound = BranchAndBound(Graph(mx,my, neighborhood))
branch_bound.compute_path(
        id_start=0,
        id_goal=8,
        budget=8,
        path=[np.array([0,0])])