from dataclasses import dataclass
from typing import Tuple, FrozenSet, Union, Optional
from p import Variable

@dataclass(frozen = True, eq = True)
class PathEntry:
    variable : Variable
    arrow : str

@dataclass(frozen = True, eq = True)
class Path:
    path : Tuple[Variable]
    arrows : Tuple[str]

    def grow(self, variable : Variable, arrow : str):
        return Path( (*self.path, variable), (*self.arrows, arrow))

    def tip(self):
        return PathEntry(self.path[-1], self.arrows[-1])

    def head(self):
        return PathEntry(self.path[0], self.arrows[0])

    def path_is_blocked(self, blockers : FrozenSet[Variable]):
        last_variable,last_arrow = None,None
        for variable,arrow in zip(self.path,self.arrows):
            if last_variable is not None:
                variable_blocked = last_variable in blockers
                d_separated_triple = Path._d_separated_triple((last_arrow,arrow), variable_blocked)
                if d_separated_triple:
                    return True
            last_variable,last_arrow = variable,arrow
        return False

    def path_blockers(self, current_adjustment_set : Optional[FrozenSet[Variable]] = None, latents : Optional[FrozenSet[Variable]] = None):
        """
            The set of variables for which the path is blocked, given the current_adjustment_set
            Not all variables given will be *necessary* to block the path, especially if the current_adjustment_set
            already contains a sufficient blocker
        """
        current_adjustment_set = current_adjustment_set or frozenset()
        latents = latents or frozenset()

        path_blockers = set()
        path_variables = self.path

        for i,variable in enumerate(path_variables):
            if i == 0 or i == (len(path_variables) - 1):
                continue
            if variable in current_adjustment_set or variable in latents:
                continue
            if self.path_is_blocked(blockers = current_adjustment_set | frozenset({ variable })):
                path_blockers.add(variable)
        
        return frozenset(path_blockers)
        
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

    def __len__(self):
        return len(self.path)

    def __str__(self):
        string = []
        for (variable,arrow) in zip(self.path, self.arrows):
            if arrow is not None:
                string.append(arrow)
            string.append(variable)
        return "".join(map(str,string))