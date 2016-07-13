from icc.studprogs.common import *

class Loader(BaseLoader):
    """Loads text and divides it on [paragraph] lokens.
    """

    def lines(self):
        """
        
        •
        -
        
        """
        linequeue=[]
        for line in self.file:
            if self._skip>0:
                self._skip-=1
                continue
            if line.startswith(b"\x0c"):
                line=line.lstrip(b"\x0c")

                prev=linequeue.pop()
                if prev==paragraph_symbol:  # must be an empty string
                    prev=linequeue.pop()
                    try:
                        int(prev.strip())
                    except ValueError:
                        linequeue.append(prev)
                else:
                    linequeue.append(prev)

                linequeue.append(page_symbol)

            uniline=line.decode(self.encoding)
            if uniline.strip():
                linequeue.append(uniline)
            elif linequeue[-1]!=paragraph_symbol:
                linequeue.append(paragraph_symbol)
            if len(linequeue)<10:
                continue
            yield linequeue.pop(0)

        yield from linequeue
