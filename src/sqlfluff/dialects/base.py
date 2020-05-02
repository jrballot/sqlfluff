"""Defines the base dialect class."""


class Dialect:
    """Serves as the basis for runtime resolution of Grammar.

    Args:
        name (:obj:`str`): The name of the dialect, used for lookup.
        lexer_struct (iterable of :obj:`tuple`): A structure defining
            the lexing config for this dialect.

    """
    def __init__(self, name, lexer_struct=None, library=None):
        self._library = library or {}
        self.name = name
        self.lexer_struct = lexer_struct

    def copy_as(self, name):
        """Copy this dialect and create a new one with a different name.

        This is the primary method for inheritance, after which, the
        `replace` method can be used to override particular rules.
        """
        return self.__class__(
            name=name,
            library=self._library.copy(),
            lexer_struct=self.lexer_struct.copy()
        )

    def segment(self):
        """This is the decorator for elements, it should be called as a method.

        e.g.
        @dialect.segment()
        class SomeSegment(BaseSegment):
            blah blah blah

        """
        def segment_wrap(cls):
            """Wrap a segment and register it against the dialect."""
            n = cls.__name__
            if n in self._library:
                raise ValueError("{0!r} is already registered in {1!r}".format(n, self))
            self._library[n] = cls
            # Pass it back after registering it
            return cls
        # return the wrapping function
        return segment_wrap

    def add(self, **kwargs):
        """Add a segment to the dialect directly.

        This is the alternative to the decorator route, most useful for segments
        defined using `make`. Segments are passed in as kwargs.

        e.g.
        dialect.add(SomeSegment=KeyworkSegment.make(blah, blah, blah))

        Note that mutiple segments can be added in the same call as this method
        will iterate through the kwargs
        """
        for n in kwargs:
            if n in self._library:
                raise ValueError("{0!r} is already registered in {1!r}".format(n, self))
            self._library[n] = kwargs[n]

    def replace(self, **kwargs):
        """Override a segment on the dialect directly.

        Usage is very similar to add, but elements specfied must already exist.
        """
        for n in kwargs:
            if n not in self._library:
                raise ValueError("{0!r} is not already registered in {1!r}".format(n, self))
            self._library[n] = kwargs[n]

    def ref(self, name):
        """Return an object which acts as a late binding reference to the element named."""
        if name in self._library:
            res = self._library[name]
            if res:
                return res
            else:
                raise ValueError(
                    "Unexpected Null response while fetching {0!r} from {1}".format(
                        name, self.name))
        else:
            raise RuntimeError(
                "Grammar refers to {0!r} which was not found in the {1} dialect".format(
                    name, self.name))

    def set_lexer_struct(self, lexer_struct):
        """Set the lexer struct for the dialect.

        This is what is used for base dialects. For derived dialects
        (which don't exist yet) the assumption is that we'll introduce
        some kind of *patch* function which could be used to mutate
        an existing `lexer_struct`.
        """
        self.lexer_struct = lexer_struct

    def get_lexer_struct(self):
        """Fetch the lexer struct for this dialect."""
        if self.lexer_struct:
            return self.lexer_struct
        else:
            raise ValueError(
                "Lexing struct has not been set for dialect {0}".format(
                    self))

    def patch_lexer_struct(self, lexer_patch):
        """Patch an existing lexer struct.

        Used to edit the lexer of a sub-dialect.
        """
        buff = []
        if not self.lexer_struct:
            raise ValueError("Lexer struct must be defined before it can be patched!")

        # Make a new data struct for lookups
        patch_dict = {elem[0]: elem for elem in lexer_patch}

        for elem in self.lexer_struct:
            if elem[0] in patch_dict:
                buff.append(patch_dict[elem[0]])
            else:
                buff.append(elem)
        # Overwrite with the buffer once we're done
        self.lexer_struct = buff

    def insert_lexer_struct(self, lexer_patch, before):
        """Insert new records into an existing lexer struct.

        Used to edit the lexer of a sub-dialect. The patch is
        inserted *before* whichever element is named in `before`.
        """
        buff = []
        found = False
        if not self.lexer_struct:
            raise ValueError("Lexer struct must be defined before it can be patched!")

        for elem in self.lexer_struct:
            if elem[0] == before:
                found = True
                for patch in lexer_patch:
                    buff.append(patch)
                buff.append(elem)
            else:
                buff.append(elem)

        if not found:
            raise ValueError("Lexer struct insert before '%s' failed because tag never found.")
        # Overwrite with the buffer once we're done
        self.lexer_struct = buff
