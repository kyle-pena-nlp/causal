from dataclasses import dataclass
from typing import FrozenSet, Union, Tuple, Dict, Union, Iterable
from collections import Counter, defaultdict
from variable import Variable
from structural_equation import StructuralEquation
from util import _ensure_is_frozen_set, _parsed_frozenset, ParseableAsVariableFrozenSet
import re

@dataclass(frozen = True, eq = True)
class Graph:

    variables : FrozenSet[Variable]

    # name of Y => eq :: Y = f(X1,X2,...)
    structural_equations : FrozenSet[StructuralEquation] 

    #def __post_init__(self):
    #    self.variables = _ensure_is_frozen_set(self.variables)
    #    self.structural_equations = _ensure_is_frozen_set(self.structural_equations)

    @staticmethod
    def parse(g : str):

        variables = set()
        parents = defaultdict(lambda: set())
        tokens = re.split(r"[;\r\n]", g)
        
        for token in tokens:
            token = token.strip()
            if '<-' in token or '->' in token:
                if '<-' in token:
                    rhs,params = token.split('<-')
                else:
                    params,rhs = token.split('->')
                rhs = Variable(rhs.strip())
                variables.add(rhs)
                for p in params.split(","):
                    p = Variable(p.strip())
                    parents[rhs].add(p)
                    variables.add(p)
            else:
                list_of_variables = token
                for variable in list_of_variables.split(","):
                    variables.add(Variable(variable.strip()))

        structural_equations = set()
        for variable in variables:
            if variable in parents:
                structural_equations.add(StructuralEquation(frozenset(parents[variable]), variable))

        return Graph(variables=variables,structural_equations=structural_equations)

    def __post_init__(self):
        valid,err = self.validate()
        if not valid:
            raise Exception(err)
    
    def _all_variables_declared(self):
        for structural_equation in self.structural_equations:
            for variable in structural_equation.X:
                if variable not in self.variables:
                    return False, "Undeclared variable '{}' appearing in structural equation".format(variable)
            if structural_equation.Y not in self.variables:
                return False, "Undeclared variable '{}' appearing in structural equation".format(structural_equation.Y)
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
        for variable in self.variables:
            if self._has_cycle(variable):
                return False, "'{}' appears in a cycle".format(variable)
        return True,None

    def _has_cycle(self, x : Variable):
        visited = { x }
        queue = [ x ]
        while len(queue) > 0:
            x_ = queue.pop()
            for child in self.children({ x_ }):
                if child == x:
                    return True
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
        return False


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

        return True,None

    def conditionally_independent(self, Y : ParseableAsVariableFrozenSet, Z : ParseableAsVariableFrozenSet, W: Union[None,ParseableAsVariableFrozenSet]):
        if W is None:
            W = frozenset()
        return self._conditionally_independent(_parsed_frozenset(Y,Variable), _parsed_frozenset(Z,Variable), _parsed_frozenset(W,Variable))

    def _conditionally_independent(self, Y : FrozenSet[Variable], Z : FrozenSet[Variable], W : FrozenSet[Variable] = None):
        return not (Z & self._reachable_from(Y, W))
    
    def reachable_from(self, X : ParseableAsVariableFrozenSet, W : Union[None,ParseableAsVariableFrozenSet] = None):
        if W is None:
            W = frozenset()
        return self._reachable_from(_parsed_frozenset(X,Variable), _parsed_frozenset(W,Variable))

    def _reachable_from(self, X : FrozenSet[Variable], W : FrozenSet[Variable]):

        """
            Apply the d-separability critera to determine what nodes are reachable from X
        """
        reachable = set()
        for x in X:
            # TODO: should I include self?
            self._reachable_from_rec(x, W, [ x ], [ None ], reachable)
        return reachable

    def _reachable_from_rec(self, x : Variable, W: FrozenSet[Variable], path : list, path_arrows : list, reachable : set()):
        
        for p in self.parents({ x }):
            
            # Paths cannot self-intersect
            if p in path:
                continue
            
            this_arrow = '<-'
            last_arrow = path_arrows[-1]
            last_variable = path[-1]
            arrows = (last_arrow,this_arrow)
            blocked = last_variable in W
            
            if not Graph._d_separated_triple(arrows,blocked):
                reachable.add(p)
                self._reachable_from_rec(p, W, path + [p], path_arrows + [this_arrow], reachable)

        for c in self.children({ x }):

            # Paths cannot self-intersect
            if c in path:
                continue
            
            this_arrow = '->'
            last_arrow = path_arrows[-1]
            last_variable = path[-1]            
            arrows = (last_arrow,this_arrow)
            blocked = last_variable in W

            if not Graph._d_separated_triple(arrows,blocked):
                reachable.add(c)
                self._reachable_from_rec(c, W, path + [c], path_arrows + [this_arrow], reachable)
                

        
    @staticmethod
    def _d_separated_triple(arrows : Tuple[Union[str,None],str], blocked : bool):
        a1,a2 = arrows
        if a1 is None:
            return False
        elif a1 == '->' and a2 == '->' and not blocked:
            return False
        elif a1 == '->' and a2 == '->' and blocked:
            return True
        elif a1 == '->' and a2 == '<-' and not blocked:
            return True
        elif a1 == '->' and a2 == '<-' and blocked:
            return False
        elif a1 == '<-' and a2 == '->' and not blocked:
            return False
        elif a1 == '<-' and a2 == '->' and blocked:
            return True
        elif a1 == '<-' and a2 == '<-' and not blocked:
            return False
        elif a1 == '<-' and a2 == '<-' and blocked:
            return True
        else:
            raise Exception("Programmer Error - unrecognized triple: A{}B(blocked={}){}C".format(a1,blocked,a2))


    # GRAPH MUTILATION OPERATION
    def orphan(self, X : FrozenSet[Variable]) -> 'Graph':
        # Remove arrows pointing into X(s)
        truncated_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.Y in X:
                pass
            else:
                truncated_structural_equations.add(structural_equation)
        return Graph(self.variables, truncated_structural_equations)

    # GRAPH MUTILATION OPERATION
    def bereave(self, X : FrozenSet[Variable]) -> 'Graph':
        # Remove arrows pointing out of X(s)
        truncated_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.X & X:
                structural_equation = structural_equation
            else:
                truncated_structural_equations.add(structural_equation)
        return Graph(self.variables, truncated_structural_equations)

    # GRAPH RELATIONSHIP OPERATION
    def ancestors(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        parents = set()
        queue = list(self.parents(X))
        visited = set()
        while len(queue) > 0:
            x = queue.pop()
            parents.add(x)
            visited.add(x)
            for parent in self.parents({ x }):
                if parent not in visited:
                    queue.append(parent)
        return parents

    # GRAPH RELATIONSHIP OPERATION
    def parents(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        parents = set()
        for x in X:
            for eq in self.structural_equations:
                if eq.Y == x:
                    for x_ in eq.X:
                        parents.add(x_)
        return parents

    # GRAPH RELATIONSHIP OPERATION
    def children(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        children = set()
        for x in X:
            for eq in self.structural_equations:
                if x in eq.X:
                    children.add(eq.Y)
        return children

    # GRAPH RELATIONSHIP OPERATION
    def descendants(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        children = set()
        queue = list(self.children(X))
        visited = set()
        while len(queue) > 0:
            x = queue.pop()
            children.add(x)
            visited.add(x)
            for child in self.children({ x }):
                if child not in visited:
                    queue.append(child)
        return children


    def __str__(self):
        struct_eq_variables = set()
        for eq in self.structural_equations:
            struct_eq_variables.add(eq.Y)
            struct_eq_variables.update(eq.X)
        isolated_variables = self.variables - struct_eq_variables
        if len(isolated_variables) == 0:
            return ";".join(sorted(map(str,self.structural_equations)))
        else:
            return ";".join(sorted(map(str,self.structural_equations)) + sorted(map(str,isolated_variables)))



if __name__ == "__main__":
    g = Graph.parse("X->Y;Y<-Z")
    g.reachable_from({ Variable("Z") }, set())