from django.core.management.base import BaseCommand

from regluit.core import bookloader

class Command(BaseCommand):
    help = "load books based on a text file of ISBNs"
    args = "<filename>"

    def handle(self, filename, **options):
        for isbn in open(filename):
            isbn = isbn.strip()
            edition = bookloader.add_by_isbn(isbn)
            if edition:
                print "loaded %s as %s" % (isbn, edition)
            else:
                print "failed to load book for %s" % isbn
