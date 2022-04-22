
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