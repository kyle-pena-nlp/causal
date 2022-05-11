from dataclasses import dataclass, field
from itertools import product, combinations, permutations
from typing import FrozenSet, Iterable, Optional, Set, Dict, List
from collections import Counter, defaultdict
import re
from p import P, Variable, Product
from path import Path
from structural_equation import StructuralEquation
from argparse import ArgumentParser
from parseable import Parseable

@dataclass(frozen = True, eq = True)
class Graph:

    # All variables in the structural equations must appear in this list
    variables : FrozenSet[Variable]
    structural_equations : FrozenSet[StructuralEquation]

    # A cache of parent and child relationships to speed up computations
    _children    : Dict[Variable,Set[Variable]] = field(default_factory = dict, init = False, compare = False, hash = False)
    _parents     : Dict[Variable,Set[Variable]] = field(default_factory = dict, init = False, compare = False, hash = False)
    _ancestors   : Dict[Variable,Set[Variable]] = field(default_factory = dict, init = False, compare = False, hash = False)
    _descendants : Dict[Variable,Set[Variable]] = field(default_factory = dict, init = False, compare = False, hash = False)

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
        self._cache_node_relationships()
        valid,err = self.validate()
        if not valid:
            raise Exception(err)

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

    # TODO: factorize using conditionals
    def joint_distribution(self):
        terms = set()
        for variable in self.variables:
            parents = self.parents({ variable })
            term = P(Y = frozenset({variable}), do = frozenset({}), Z = parents)
            terms.add(term)
        return Product(frozenset(terms))

    def conditionally_independent(self, Y , Z, W = None):
        if W is None:
            W = frozenset()
        complete_paths = set()
        paths = { Path(path = (y,), arrows = (None,)) for y in Y }
        while len(paths) > 0:
            self._grow_paths(destination_set = Z, paths = paths, completed_paths = complete_paths, directions = ('<-','->'), adjustment_set=W)
            if len(complete_paths) > 0:
                return False
        return True
    
    # GRAPH MUTILATION OPERATION
    def orphan(self, X : FrozenSet[Variable]) -> 'Graph':
        # Remove arrows pointing into X
        truncated_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.Y in X:
                pass
            else:
                truncated_structural_equations.add(structural_equation)
        return Graph(self.variables, truncated_structural_equations)

    # GRAPH MUTILATION OPERATION
    def bereave(self, X : FrozenSet[Variable]) -> 'Graph':
        # Remove arrows pointing out of X
        modified_structural_equations = set()
        for structural_equation in self.structural_equations:
            if structural_equation.X & X:
                structural_equation = StructuralEquation(X = structural_equation.X - X, Y = structural_equation.Y)
            modified_structural_equations.add(structural_equation)
        return Graph(self.variables, modified_structural_equations)

    # GRAPH RELATIONSHIP OPERATION
    def parents(self, X : Iterable[Variable]) -> FrozenSet[Variable]:
        parents_ = set()
        for x in X:
            parents_ |= self._parents[x]
        return frozenset(parents_)
        """
        parents = set()
        for x in X:
            for eq in self.structural_equations:
                if eq.Y == x:
                    for x_ in eq.X:
                        parents.add(x_)
        return frozenset(parents)
        """

    # GRAPH RELATIONSHIP OPERATION
    def children(self, X : Iterable[Variable]) -> FrozenSet[Variable]:
        children_ = set()
        for x in X:
            children_ |= self._children[x]
        return frozenset(children_)
        """
        children = set()
        for x in X:
            for eq in self.structural_equations:
                if x in eq.X:
                    children.add(eq.Y)
        return frozenset(children)
        """

    # GRAPH RELATIONSHIP OPERATION
    def ancestors(self, X : Iterable[Variable]) -> FrozenSet[Variable]:
        # TODO: replace with repeated calls to _grow_paths?
        ancestors_ = set()
        for x in X:
            ancestors_ |= self._ancestors[x]
        return frozenset(ancestors_)
        """
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
        """

    # GRAPH RELATIONSHIP OPERATION
    def descendants(self, X : Iterable[Variable]) -> FrozenSet[Variable]:
        # TODO: replace with repeated calls to _grow_paths?     
        descendants_ = set()
        for x in X:
            descendants_ |= self._descendants[x]
        return frozenset(descendants_)
        """
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
        """
    # Per Shpister, Pearl 2006
    def root_set(self):
        results = []
        for variable in self.variables:
            if not self.descendants([variable]):
                results.append(variable)
        return frozenset(results)

    # Per Shpister, Pearl 2006
    def sub_graph(self, Y : Iterable[Variable]):

        parents = {}
        for y in Y:
            if y not in self.variables:
                raise Exception("{} does not exist in graph".format(y))
            parents[y] = self.parents[y] & Y
        
        structural_equations = set()
        for variable in Y:
            if variable in parents and len(parents[variable]):
                structural_equations.add(StructuralEquation(frozenset(parents[variable]), variable))

        return Graph(variables=Y, structural_equations=structural_equations)

    # Per Shpister, Pearl 2006
    def maximal_C_components(self, latents : FrozenSet[Variable]):
        C_components = {}
        variables = set(self.variables)
        # Algorithm:
        """
            Pick an arbitrary variable, make it a C-component
            Grow the C-component until you can't anymore.
            Then start a new C-component
            When you've consumed all the variables, terminate and return the C-components
        """
        while len(variables) > 0:
            C_component = { variables.pop() }
            while True:
                growth_set = self.bidirected_edge_neighbors(C_component, latents) - C_component
                if len(growth_set) > 0:
                    C_component |= growth_set
                    variables -= growth_set
                else:
                    C_components.add(C_component)
                    break
        return frozenset(C_components)

    def bidirected_edge_neighbors(self, C_component : Set[Variable], latents : FrozenSet[Variable]):
        results = {}
        for variable in C_component:
            latent_parents = latents & self.parents[variable]
            for latent_parent in latent_parents:
                for parent_latent_parent in self.parents[latent_parent]:
                    results.add(parent_latent_parent)
                for child_latent_parent in self.children[latent_parent]:
                    results.add(child_latent_parent)
            latent_children = latents & self.children[variable]
            for latent_child in latent_children:
                for parent_latent_child in self.parents[latent_child]:
                    results.add(parent_latent_child)
                for child_latent_child in self.children[latent_child]:
                    results.add(child_latent_child)
        return frozenset((results - C_component) - latents)

    def _gen_blocker_sets(self, paths : FrozenSet[Path], current_adjustment_set : FrozenSet[Variable], latents : FrozenSet[Variable]):
        """
            Find all sets of blockers that block all paths, given a current (possibly empty) adjustment set and a set of unobservable latents
        """
        
        # Find the set of blocking variables in each path
        blockers_per_path = [ list(path.path_blockers(current_adjustment_set = current_adjustment_set, latents = latents)) for path in paths ]
        
        # Order each set in terms of how common that variable appears in all blocking sets
        most_common_blockers = [ blocker for (blocker,count) in Counter([ path_blocker for path_blockers in blockers_per_path for path_blocker in path_blockers ]).most_common() ]
        for path_blockers in blockers_per_path:
            path_blockers.sort(key = lambda blocker: most_common_blockers.index(blocker))

        # Yield unique generated blocker sets.
        # The ordering as imposed above will tend to yield the most economical blocker sets first
        blocker_sets_so_far = set()
        for blocker_set in product(*blockers_per_path):
            # Test for sufficiency
            if not all(path.path_is_blocked(blockers = blocker_set) for path in paths):
                continue
            blocker_set = frozenset(blocker_set)
            if blocker_set not in blocker_sets_so_far:
                blocker_sets_so_far.add(blocker_set)
                yield blocker_set

    def gen_sufficient_backdoor_adjustment_sets(self, X: FrozenSet[Variable], Y : FrozenSet[Variable], latents : Optional[FrozenSet[Variable]] = None,
            current_adjustment_set : Optional[FrozenSet[Variable]] = None) -> \
        Iterable[FrozenSet[Variable]]:
        
        latents = latents or frozenset()
        current_adjustment_set = current_adjustment_set or frozenset()

        backdoor_paths = self.backdoor_paths(X, Y)
        for blocker_set in self._gen_blocker_sets(paths = backdoor_paths, current_adjustment_set = current_adjustment_set, latents = latents):
            yield blocker_set

    def gen_sufficient_mediation_set(self, X : FrozenSet[Variable], Y: FrozenSet[Variable], latents : Optional[FrozenSet[Variable]] = None,
            current_adjustment_set : Optional[FrozenSet[Variable]] = None) -> \
        Iterable[FrozenSet[Variable]]:
        
        latents = latents or frozenset()
        current_adjustment_set = current_adjustment_set or frozenset()

        causal_paths = self.causal_paths(X,Y)
        for blocker_set in self._gen_blocker_sets(paths = causal_paths, current_adjustment_set = current_adjustment_set, latents = latents):
            yield blocker_set

    def gen_adjustment_sets(self, X: FrozenSet[Variable], Y: FrozenSet[Variable], latents : Optional[FrozenSet[Variable]] = None,
            current_adjustment_set : Optional[FrozenSet[Variable]] = None) -> \
        Iterable[FrozenSet[Variable]]:

        latents = latents or frozenset()
        current_adjustment_set = current_adjustment_set or frozenset()

        paths = self.paths(X,Y)
        for blocker_set in self._gen_blocker_sets(paths = paths, current_adjustment_set = frozenset(), latents = latents):
            yield blocker_set

    def paths(self, X : FrozenSet[Variable], Y : FrozenSet[Variable], W : Optional[FrozenSet[Variable]] = None) -> FrozenSet[Path]:
        W = W or frozenset()
        paths = { Path(path = (x,), arrows = (None,)) for x in X }
        completed_paths = set()
        while len(paths) > 0:
            self._grow_paths(Y, paths, completed_paths, directions = ('->','<-'), adjustment_set = W)
        return frozenset(completed_paths)

    def causal_paths(self, X : FrozenSet[Variable], Y: FrozenSet[Variable], W: Optional[FrozenSet[Variable]] = None) -> FrozenSet[Path]:
        W = W or frozenset()
        paths = { Path(path = (x,), arrows = (None,)) for x in X } 
        completed_paths = set()
        while len(paths) > 0:
            self._grow_paths(Y, paths, completed_paths, directions = ('->',), adjustment_set = W)
        return frozenset(completed_paths)

    def backdoor_paths(self, X: FrozenSet[Variable], Y: FrozenSet[Variable], W: Optional[FrozenSet[Variable]] = None) -> FrozenSet[Path]:
        W = W or None
        paths = { Path(path = (x,), arrows = (None,)) for x in X }
        completed_paths = set()
        self._grow_paths(Y, paths, completed_paths, directions = ('<-',))
        while len(paths) > 0:
            self._grow_paths(Y, paths, completed_paths, directions = ('<-','->'), adjustment_set = W)
        return frozenset(completed_paths)

    def gen_admissible_orderings(self, X : Iterable[Variable]):

        # My tactic here is to grow the admissible orderings inductively
        # and branch (enqueue) when it is possible to place an element in more than one location

        x = sorted(X)[0]
        queue = [(x,)]
        visited = set()
        while len(queue) > 0:

            # Get an ordering, mark it as visited
            ordering = queue.pop()
            visited.add(ordering)            

            # If the ordering is complete, yield it
            if len(ordering) == len(X):
                yield ordering
                continue

            # Find all variables not currently in the ordering
            X_ = sorted(set(X) - set(ordering))

            # For each one
            for x_ in X_:

                # Examine all positions in which we could splice x_ into the existing ordering
                for splice_idx in range(len(ordering)+1):

                    before,after = ordering[:splice_idx], ordering[splice_idx:]

                    # To splice x_ between 'before' and 'after', two conditions must be met:
                    #   1. every x in 'before' must be a non-descendant of x_ 
                    #       (we already know that every x in 'before' is a non-descendant of every x' in 'after' by inductively)
                    #   2. x_ not be a non-descendant of every x in 'after'
                    #       (we already know that every x in 'before' is a non-descendant of every x' in 'after' by induction)

                    # Condition 1
                    every_before_non_descendant_x_ = not (set(before) & self.descendants({x_}))
                    if not every_before_non_descendant_x_:
                        # We can break here rather than continue, because if we move the splice idx forward we only grow 'before'
                        # And thus the condition of non-intersection of 'before' and the descendants of x_ will still fail.
                        break

                    # Condition 2
                    x__is_non_descendant_of_every_x_in_after = x_ not in self.descendants(after)
                    if not x__is_non_descendant_of_every_x_in_after:
                        continue
                    
                    # Splice together the new order, enqueue it if it hasn't been visited
                    ordering_ = (*before, x_, *after)
                    if ordering_ not in visited:
                        queue.append(ordering_)

    def _grow_paths(self, 
        destination_set : FrozenSet[Variable], 
        paths : Set[Path], 
        completed_paths : Set[Path],
        directions = ('->','<-'),
        adjustment_set : FrozenSet[Variable] = None):

        """
            Grow a path (in any specified direction) until it either:
                1) Encounters d-separation
                2) Reaches the destination set

            When a path reaches a destination set, add it to the completed_paths

            This method is a workhorse.  For example, we can get all causal descendants
            by repeatedly calling _grow_paths with directions = ('->',) and an empty adjustment set.
        """

        adjustment_set = adjustment_set or frozenset()
        
        new_paths = set()

        # This work loop would be a good target for parallelism, should it be needed
        while len(paths) > 0:

            path = paths.pop()
            last_variable = path.path[-1]
            last_arrow    = path.arrows[-1]
            
            if '->' in directions:
            
                for child in self.children({ last_variable }):
                    
                    # Paths cannot self-intersect
                    if child in path.path:
                        continue

                    # Do not continue if there is d-separation
                    blocked = last_variable in adjustment_set
                    if Path._d_separated_triple((last_arrow, '->'), blocked):
                        continue

                    # Grow the path to include the child
                    path_ = path.grow(child, '->') 


                    # If this path reaches the destination set, add it to the completed paths          
                    if child in destination_set:
                        completed_paths.add(path_)
                    
                    # Otherwise, enqueue this branch
                    elif path_ not in paths:
                        new_paths.add(path_)
                    
            if '<-' in directions:
                for parent in self.parents({ last_variable }):

                    # Paths cannot self-intersect
                    if parent in path.path:
                        continue

                    # Check for d-separation
                    blocked = last_variable in adjustment_set
                    if Path._d_separated_triple((last_arrow, '<-'), blocked):
                        continue
                    
                    # Grow the path to include the parent
                    path_ = path.grow(parent, '<-')      

                    # If this path reaches the destination set, add it to the completed paths            
                    if parent in destination_set:
                        completed_paths.add(path_)

                    # Otherwise, enqueue this branch
                    elif path_ not in paths:
                        new_paths.add(path_)
    
        paths |= new_paths

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

    def _cache_node_relationships(self):

        # Cache parents and children
        for variable in self.variables:
            self._children[variable] = set()
            self._parents[variable] = set()
            for eq in self.structural_equations:
                if variable == eq.Y:
                    self._parents[variable] = (eq.X)
                if variable in eq.X:
                    self._children[variable].add(eq.Y)

        # Cache ancestors
        for variable in self.variables:
            self._ancestors[variable] = set()
            queue = list(self._parents[variable]) # seed queue with parents rather than self, because self is not ancestor of self
            while len(queue) > 0:
                ancestor = queue.pop()
                if ancestor in self._ancestors[variable]:
                    continue
                self._ancestors[variable].add(ancestor)
                for parent in self._parents[ancestor]:
                    queue.append(parent)
        
        # Cache descendants
        for variable in self.variables:
            self._descendants[variable] = set()
            queue = list(self._children[variable]) # seed queue with children rather than self, because self is not descendant of self
            while len(queue) > 0:
                descendant = queue.pop()
                if descendant in self._descendants[variable]:
                    continue
                self._descendants[variable].add(descendant)
                for child in self._children[descendant]:
                    queue.append(child)

    
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
    
    parser = ArgumentParser()
    parser.add_argument("--graph", type = str, required = False, default = "Q->X;X->Y;Q->R;Q->S;R->Y;S->Y;W")
    parser.add_argument("--treatment", type = str, required = False, default = "X,Y,Q,W")
    parser.add_argument("--exposure", type = str, required = False, default = "Y")
    parser.add_argument("--latents", type = str, required = False, default = "")
    parser.add_argument("--adjustment_set", type = str, required = False, default = "")
    parser.add_argument("--method", type = str, required = False, default = "admissible_orderings")
    args = parser.parse_args()

    g : Graph = Graph.parse(args.graph)
    X : FrozenSet[Variable] = Parseable.parse_list(Variable, args.treatment)
    Y : FrozenSet[Variable] = Parseable.parse_list(Variable, args.exposure)
    W : FrozenSet[Variable] = Parseable.parse_list(Variable, args.adjustment_set)
    latents : FrozenSet[Variable] = Parseable.parse_list(Variable, args.latents)
    method = args.method
    
    def _print_things(things):
        print(", ".join(map(str,things)))

    #for path in g.paths(X,Y):
    #    print(path)
    if method == "parents":
        _print_things(g.parents(X))
    elif method == "ancestors":
        _print_things(g.ancestors(X))
    elif method == "children":
        _print_things(g.children(X))
    elif method == "descendants":
        _print_things(g.descendants(X))
    elif method == "paths":
        _print_things(g.paths(X, Y, W))
    elif method == "causal_paths":
        _print_things(g.causal_paths(X,Y,W))
    elif method == "backdoor_paths":
        _print_things(g.backdoor_paths(X,Y,W))
    elif method == "joint_distribution":
        print(g.joint_distribution())
    elif method == "conditionally_independent":
        print(g.conditionally_independent(X, Y, W))
    elif method == "backdoor_adjustment_sets":
        for backdoor_adjustment_set in g.gen_sufficient_backdoor_adjustment_sets(X, Y, latents = latents):
            _print_things(backdoor_adjustment_set)
    elif method == "causal_mediation_sets":
        for causal_mediation_set in g.gen_sufficient_mediation_set(X, Y, latents = latents):
            _print_things(causal_mediation_set)
    elif method == "adjustment_sets":
        for adjustment_set in g.gen_adjustment_sets(X, Y, latents = latents):
            _print_things(adjustment_set)
    elif method == "admissible_orderings":
        for admissible_ordering in g.gen_admissible_orderings(X):
            _print_things(admissible_ordering)
