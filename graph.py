from dataclasses import dataclass
from typing import Set, Union, Tuple, Dict
from collections import Counter

from variable import Variable
from structural_equation import StructuralEquation


@dataclass
class Graph:

    variables : Set[Variable]

    # name of Y => eq :: Y = f(X1,X2,...)
    structural_equations : Set[StructuralEquation] 

    def _all_variables_declared(self):
        for structural_equation in self.structural_equations.items():
            for variable in structural_equation.X + (structural_equation.Y,):
                if variable not in self.variables:
                    return False, "Undeclared variable '{}' appearing in structural equation".format(variable)
        return True,None

    def _unique_outcomes(self):
        counter = Counter([ eq.Y for eq in self.structural_equations ])
        for (variable,count) in counter.most_common():
            if count <= 1:
                break
            else:
                return False,"Variable '{}' occurs as an outcome in more than one structural equation".format(variable)
        return True,None

    def _acyclic(self):
        for variable in self.variableS:
            if self._has_cycle(self, variable):
                return False, "'{}' appears in a cycle".format(variable)
        return True,None

    def _has_cycle(self, X):
        visited = set()
        queue = [ X ]
        while len(queue) > 0:
            x = queue.pop()
            for child in self.children(x):
                if child == X:
                    return False
                if child not in visited:
                    visited.add(child)
                    queue.append(child)


    def validate(self):
        # TODO: check for at most 1 equation per variable
        # TODO: check for acylicity

        valid,err = self._unique_outcomes()
        if not valid:
            return False,err

        valid,err = self._all_variables_declared()
        if not valid:
            return False,err

        valid,err = self._acyclic()
        if not valid:
            return False,err

    def conditionally_independent(self, Y : Set[Variable], Z : Set[Variable], W : Set[Variable]):
        return not (Z & self.reachable_variables(Y, W))
    
    def reachable_variables(self, X : Set[Variable], W : Set[Variable]):

        """
            Finds all reachable variables in the graph from X given a conditioning set W
            The queue consists of tuple (A,direction1,B) and enqueues new tuples (B,direction2,C)
            when (A,direction1,B,direction2,C) is an unblocked tuple
        """

        queue,visited,reachable = [], set(),set()

        for parent in self.parents(X):
            for x in X:
                queue.append((x,parent,'<-'))
                reachable.add(parent)
        
        for child in self.children(X):
            for x in X:
                queue.append((x,child,'->'))
                reachable.add(child)

        while len(queue) > 0:
            item = queue.pop()
            visited.add(item)
            a,b,direction = item
            if direction == '<-' and b not in W:
                for c in self.children({ b }):
                    item_ = (b,c,'->')
                    if item_ not in visited:
                        queue.append(item_)
                        reachable.add(c)
                for c in self.parents({ b }):
                    item_ = (b,c,'<-')
                    if item_ not in visited:
                        queue.append(item_)
                        reachable.add(c)
            elif direction == '->':
                if b in W:
                    for c in self.parents({ b }):
                        item_ = (b,c,'<-')
                        if item_ not in visited:
                            queue.append(item_)
                            reachable.add(c)
                if b not in W:
                    for c in self.children({ b }):
                        item_ = (b,c,'->')
                        if item_ not in visited:
                            queue.append(item_)
                            reachable.add(c)
        
        return reachable


    # GRAPH MUTILATION OPERATION
    def orphan(self, X : Set[Variable]) -> 'Graph':
        # Remove arrows pointing into X(s)
        truncated_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.Y in X:
                pass
            else:
                truncated_structural_equations.add(structural_equation)
        return Graph(self.variables, truncated_structural_equations)

    # GRAPH MUTILATION OPERATION
    def bereave(self, X : Set[Variable]) -> 'Graph':
        # Remove arrows pointing out of X(s)
        truncated_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.X & X:
                structural_equation = structural_equation
            else:
                truncated_structural_equations.add(structural_equation)
        return Graph(self.variables, truncated_structural_equations)

    # GRAPH RELATIONSHIP OPERATION
    def ancestors(self, X : Set[Variable]) -> Set[Variable]:
        parents = set()
        queue = list(self.parents(X))
        visited = set()
        while len(queue) > 0:
            x = queue.pop()
            parents.add(x)
            visited.add(x)
            for parent in self.parents(x):
                if parent not in visited:
                    queue.append(parent)
        return parents

    # GRAPH RELATIONSHIP OPERATION
    def parents(self, X : Set[Variable]) -> Set[Variable]:
        parents = set()
        for x in X:
            for eq in self.structural_equations:
                if eq.Y == x:
                    for x_ in eq.X:
                        parents.add(x_)
        return parents

    # GRAPH RELATIONSHIP OPERATION
    def children(self, X : Set[Variable]) -> Set[Variable]:
        children = set()
        for x in X:
            for eq in self.structural_equations:
                if x in eq.X:
                    children.add(eq.Y)
        return children

    # GRAPH RELATIONSHIP OPERATION
    def descendants(self, X : Set[Variable]) -> Set[Variable]:
        children = set()
        queue = list(self.children(X))
        visited = set()
        while len(queue) > 0:
            x = queue.pop()
            children.add(x)
            visited.add(x)
            for child in self.children(x):
                if child not in visited:
                    queue.append(child)
        return children

