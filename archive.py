
def identifiable_with_marginalization(statement: Union[P,str], graph: Union[Graph,str]):
    statement = _parsed(statement, P)
    graph     = _parsed(graph, Graph)

    # (TODO: Way to pinpoint all sufficient conditioning sets?)
    all_possible_deconfounders = _get_all_possible_deconfounders(statement,graph)
    for deconfounding_set in _powerset(all_possible_deconfounders):
        expression = _condition_on_and_marginalize_out(statement, frozenset(deconfounding_set), graph)
        derivation = _identifiable_expression(expression, graph)
        if derivation:
            return (derivation,deconfounding_set)

def _get_all_possible_deconfounders(statement : P, graph : Graph):
    # Any variable from reachable from X and Y in G
    # but excluding X and Y, 
    # and excluding the current conditioning set
    X = statement.do
    Y = statement.Y
    return ((graph.reachable_from(X) & graph.reachable_from(Y)) - (X|Y) - statement.Z)

def _condition_on_and_marginalize_out(statement : P, Z : FrozenSet[Variable], graph : Graph):
    graph = graph.orphan(statement.do)
    statement = P(Y = statement.Y, do = statement.do, Z = statement.Z | Z)
    Pz = P(Y = Z, do = frozenset(), Z = frozenset())
    terms = [ statement, Pz ]
    """
    queue, visited, margins = list(Z), set(), set()
    while len(queue) > 0:
        z = queue.pop()
        if z in visited:
            continue
        visited.add(z)
        z = frozenset({ z })
        parents = graph.parents(z)
        z_conditional = parents - statement.do
        z_do = parents & statement.do
        terms.add(P(y = frozenset(z), do = z_do, z = z_conditional))
        for z_ in z_conditional:
            queue.append(z_)
    """
    return Marginalization(frozenset(Z), Product(terms))

def _identifiable_expression(expression : Expression, graph : Graph):
    if isinstance(expression, P):
        return identifiable(expression, graph)
    elif isinstance(expression, Product):
        return [ identifiable(term, graph) for term in expression.terms ]
    elif isinstance(expression, Marginalization):
        return _identifiable_expression(expression.expression, graph)
    else:
        raise Exception("Unknown expression type '{}'".format(type(expression)))


            # Seed the queue with (a,b,<- or ->)
            for parent in self.parents({ x }):
                queue.append((x,parent,'<-'))
            for child in self.children({ x }):
                queue.append((x,child,'->'))


            while len(queue) > 0:
                x = queue.pop(0)
                path.append(x)
                a,b,direction = x
                if direction == '<-' and b not in W:
                    for c in self.children({ b }):
                        if c in path:
                            continue
                        item_ = (b,c,'->')
                        if item_ not in visited:
                            queue.append(item_)

                            reachable.add(c)
                    for c in self.parents({ b }):
                        if c in path:
                            continue
                        item_ = (b,c,'<-')
                        if item_ not in visited:
                            queue.append(item_)
                            reachable.add(c)
                elif direction == '->':
                    if b in W:
                        for c in self.parents({ b }):
                            if c in path:
                                continue
                            item_ = (b,c,'<-')
                            if item_ not in visited:
                                queue.append(item_)
                                reachable.add(c)
                    if b not in W:
                        for c in self.children({ b }):
                            if c in path:
                                continue
                            item_ = (b,c,'->')
                            if item_ not in visited:
                                queue.append(item_)
                                reachable.add(c)                

        
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
            
        
        return reachable






    @staticmethod
    def parse(p : str):

        # TODO: a real parser.

        Y = set()
        do = set()
        Z = set()

        m = re.match("P\((.*)\)", p)
        if m:
            p = m.group(1)
        p = p.strip()
        if p == "":
            raise Exception("Must be non-empty")
        if "|" in p:
            p = p.split("|")
            for x in p[0].split(","):
                x = x.strip()
                Y.add(x)
            for x in p[1].split(","):
                x = x.strip()
                m = re.match("do\((.*)\)", x)
                if m:
                    x = m.group(1).strip()
                    do.add(x)
                else:
                    Z.add(x)
        else:
            for x in p.split(","):
                x = x.strip()
                Y.add(x)

        if len(Y) == 0:
            raise Exception("Must contain at least one variable on LHS of conditional")

        Y  = [ Variable(y) for y in Y ]
        do = [ Variable(d) for d in do ]
        Z  = [ Variable(z) for z in Z ]

        return P(Y = frozenset(Y), do = frozenset(do), Z = frozenset(Z))



    @staticmethod
    def parse(string : str):
        expressions = []
        tokens = string.split("*")
        for token in tokens:
            token = token.strip()
            if token.startswith("E["):
                expressions.add(Marginalization.parse(token))
            else:
                expressions.add(P.parse(token))
        return Product(frozenset(expressions))


    @staticmethod 
    def parse(string : str):
        m = re.match(r"E\[([^;]*);([^]]*)\]",string)
        if not m:
            raise Exception("Doesn't look like a marginalization: {}".format(string))
        p = m.group(1)
        p = P.parse(p)
        X = m.group(2)
        X = _parsed_frozenset(X, Variable)
        return Marginalization(X = X, statement = p)


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

    def backdoor_paths(self, X : Variable, Y: Variable) -> Iterable[Path]:
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


    def _grow_paths(self, 
        destination_set : FrozenSet[Variable], 
        paths : Set[Path], 
        completed_paths = Set[Path],
        directions = ('->','<-'),
        adjustment_set : FrozenSet[Variable] = None):

        adjustment_set = adjustment_set or frozenset()
        
        paths_to_grow = sorted(paths)

        while len(paths_to_grow) > 0:
            path = paths_to_grow.pop()
            tip = path[-1]
            if '->' in directions:
                for child in self.children({ tip }):
                    if child in path:
                        continue
                    path_ = path.grow(child, '->')                  
                    if child in destination_set:
                        completed_paths.add(path_)
                    elif path_ not in paths:
                        paths.add(path_)
            if '<-' in directions:
                for parent in self.parents({ tip }):
                    if parent in path:
                        continue
                    path_ = path.grow(parent, '<-')                  
                    if parent in destination_set:
                        completed_paths.add(path_)
                    elif path_ not in paths:
                        paths.add(path_)