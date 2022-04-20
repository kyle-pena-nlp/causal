
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