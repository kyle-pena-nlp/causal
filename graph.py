from dataclasses import dataclass, field
from typing import FrozenSet, Union, Tuple, Dict, Union, Iterable, List, Optional
from collections import Counter, defaultdict
import re
from p import P, Variable, Product, Quotient
from p import P
from structural_equation import StructuralEquation
from util import maybe_parse, maybe_parse_frozenset


@dataclass(frozen = True, eq = True)
class Graph:

    variables : FrozenSet[Variable]

    # name of Y => eq :: Y = f(X1,X2,...)
    structural_equations : FrozenSet[StructuralEquation]

    #def __post_init__(self):
    #    self.variables = _ensure_is_frozen_set(self.variables)
    #    self.structural_equations = _ensure_is_frozen_set(self.structural_equations)

    # TODO: replace with EBNF based parser
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
        """
            Validation: No variables appear in graph that are undeclared
        """
        for structural_equation in self.structural_equations:
            for variable in structural_equation.X:
                if variable not in self.variables:
                    return False, "Undeclared variable '{}' appearing in structural equation".format(variable)
            if structural_equation.Y not in self.variables:
                return False, "Undeclared variable '{}' appearing in structural equation".format(structural_equation.Y)
        return True,None

    def _unique_outcomes(self):
        """
            Validation: A variable appears as an outcome in at most one structural equation 
        """
        counter = Counter([ eq.Y for eq in self.structural_equations ])
        for (variable,count) in counter.most_common():
            if count <= 1:
                break
            else:
                return False,"Variable '{}' occurs as an outcome in more than one structural equation".format(variable)
        return True,None

    def _acyclic(self):
        """
            Validation: There are no cycles implied by the structural equations
        """
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
        """
            Make sure graph implied by structural equations meets assumptions
        """

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

    def joint_distribution(self):
        terms = set()
        for variable in self.variables:
            parents = self.parents({ variable })
            term = P(Y = frozenset({variable}), do = frozenset({}), Z = parents)
            terms.add(term)
        return Product(frozenset(terms))

    def conditional_distribution(self, Z: FrozenSet[Variable]):
        joint_distribution = self.joint_distribution()
        denominator_terms = { P(Y = z, do = frozenset({}), Z = frozenset({})) for z in Z }
        eliminated_terms = joint_distribution.terms & denominator_terms
        raise Exception("ConditionalProbability class?")
        #return ConditionalProbability(numerator = joint_distribution.terms - eliminated_terms, denominator = denominator_terms - eliminated_terms)

    def conditionally_independent(self, Y , Z, W = None):
        
        if W is None:
            W = frozenset()
        return self._conditionally_independent(maybe_parse_frozenset(Variable,Y), maybe_parse_frozenset(Variable,Z), maybe_parse_frozenset(Variable,W))

    def _conditionally_independent(self, Y : FrozenSet[Variable], Z : FrozenSet[Variable], W : FrozenSet[Variable] = None):
        return not (Z & self._reachable_from(Y, W))
    
    def reachable_from(self, X, W = None):
        if W is None:
            W = frozenset()
        return self._reachable_from(maybe_parse_frozenset(Variable,X), maybe_parse_frozenset(Variable,W))

    def _reachable_from(self, X : FrozenSet[Variable], W : FrozenSet[Variable]):

        """
            Apply the d-separability critera to determine what nodes are reachable from X
        """
        reachable = set()
        for x in X:
            # TODO: should I include self?
            self._reachable_from_rec(x, W, [ x ], [ None ], reachable)
        return reachable

    def _reachable_from_rec(self, x : Variable, W: FrozenSet[Variable], path : List[Variable], path_arrows : List[str], reachable : set()):
        
        for p in self.parents({ x }):
            
            # Paths cannot self-intersect
            if p in path:
                continue
            
            this_arrow = '<-'
            last_arrow = path_arrows[-1]
            last_variable = path[-1]
            arrows = (last_arrow,this_arrow)
            blocked = last_variable in W or (self.descendants({ last_variable }) & W)

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
            blocked = last_variable in W or (self.descendants({ last_variable }) & W)

            if not Graph._d_separated_triple(arrows,blocked):
                reachable.add(c)
                self._reachable_from_rec(c, W, path + [c], path_arrows + [this_arrow], reachable)
                
    def paths(self, X : Variable, Y: Variable, search_directions = ('->','<-')):
        """
            Generate all paths from X to Y, irrespective of blocking, direction, etc.
        """
        paths, arrow_paths = [], []
        path_so_far, path_arrows_so_far = [X], [None]        

        self._paths_rec(Y, path_so_far, path_arrows_so_far, paths, arrow_paths, search_directions)
        return paths, arrow_paths

    def _paths_rec(self, 
            Y : Variable, 
            path_so_far : List[Variable], path_arrows_so_far : List[str], 
            paths : List[Tuple[Variable]], arrow_paths: List[Tuple[str]],
            search_directions) -> \
        Tuple[List[Tuple[Variable]],List[Tuple[Optional[str]]]]:
        
        tip = path_so_far[-1]
        
        if '<-' in search_directions:
            for x in self.parents(frozenset({ tip })):
                if x in path_so_far:
                    continue
                elif x == Y:
                    paths.append(tuple(path_so_far + [Y]))
                    arrow_paths.append(tuple(path_arrows_so_far + ['<-']))
                else:
                    self._paths_rec(Y, path_so_far + [x], path_arrows_so_far + ['<-'], paths, arrow_paths, search_directions)
        
        if '->' in search_directions:
            for x in self.children(frozenset({ tip })):
                if x in path_so_far:
                    continue
                elif x == Y:
                    paths.append(tuple(path_so_far + [Y]))
                    arrow_paths.append(tuple(path_arrows_so_far + ['->']))
                else:
                    self._paths_rec(Y, path_so_far + [x], path_arrows_so_far + ['->'], paths, arrow_paths, search_directions)

    def backdoor_paths(self, X : Variable, Y: Variable) -> FrozenSet[Tuple[Variable]]:
        """
            Generate all backdoor paths from X to Y, irrespective of blocking, direction, etc.
        """
        paths, arrow_paths = [], []
        path_so_far, path_arrows_so_far = [X], [None]  

        for x in self.parents(frozenset({ X })):
            if x in path_so_far:
                continue
            elif x == Y:
                paths.append(tuple(path_so_far + [Y]))
                arrow_paths.append(tuple(path_arrows_so_far + ['<-']))
            else:
                self._paths_rec(Y, path_so_far + [x], path_arrows_so_far + ['<-'], paths, arrow_paths, ('<-','->'))

        return list(zip(paths, arrow_paths))

    def causal_paths(self, X : Variable, Y : Variable):
        """
            Generate all causal paths from X to Y, irrespective of blocking, direction, etc.
        """
        return self.paths(X, Y, '->')

    def path_is_blocked(self, path : Tuple[Variable], path_arrows : Tuple[Optional[str]], blockers : FrozenSet[Variable]):
        last_variable,last_arrow = None,None
        for variable,arrow in zip(path,path_arrows):
            if last_variable is not None:
                variable_blocked = last_variable in blockers
                d_separated_triple = Graph._d_separated_triple((last_arrow,arrow), variable_blocked)
                if d_separated_triple:
                    return True
            last_variable,last_arrow = variable,arrow
        return False

    def path_blockers(self, path):
        path_blockers = set()
        path_variables,path_arrows = path
        # TODO: exclude start and end
        for variable in path_variables:
            if self.path_is_blocked(path_variables, path_arrows, frozenset({ variable })):
                path_blockers.add(variable)
        return path_blockers
        
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
        modified_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.X & X:
                structural_equation = StructuralEquation(X = structural_equation.X - X, Y = structural_equation.Y)
            modified_structural_equations.add(structural_equation)
        return Graph(self.variables, modified_structural_equations)

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
        return frozenset(parents)

    # GRAPH RELATIONSHIP OPERATION
    def children(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        children = set()
        for x in X:
            for eq in self.structural_equations:
                if x in eq.X:
                    children.add(eq.Y)
        return frozenset(children)

    def neighbors(self, X : FrozenSet[Variable]) -> FrozenSet[Variable]:
        # No spouses, even though that abuses the metaphor a bit
        return self.parents(X) | self.children(X)

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