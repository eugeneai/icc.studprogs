#import icc.studprogs
import icc.studprogs.textloader as textloader
#import pybison
from pkg_resources import resource_stream

from itertools import islice
import sys

package=__name__
TEST_FILE=resource_stream("icc.studprogs","data/059285.txt")

def main(stream, limit):
    """

    Arguments:
    - `stream`: open stream to learn from
    """
    loader=textloader.Loader(stream)
    for lexem in islice(loader.paragraphs(), limit):
        print (lexem)


if __name__=="__main__":
    limit = 1000000
    main(TEST_FILE, limit)
    quit()
