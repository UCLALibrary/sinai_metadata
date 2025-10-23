from migrate import parse

class TestSplitByDelim:
    def test_no_delim(self):
        s = "This is text"
        assert s == parse.split_by_delim(data=s, delim=[], quotechar=None)
    
    def test_single_delim(self):
        s = "This is text$delmited text$and more text"
        l = ["This is text", "delmited text", "and more text"]
        assert l == parse.split_by_delim(data=s, delim=["$"], quotechar=None)

    def test_double_delim(self):
        s = "This is text$with delimited text#inside of delimited text$And more text#with its own delimited text$And even more for fun"
        l = [["This is text"], ["with delimited text", "inside of delimited text"], ["And more text", "with its own delimited text"], ["And even more for fun"]]
        assert l == parse.split_by_delim(data=s, delim=["$", "#"], quotechar=None)

    def test_two_delim_but_second_absent(self):
        s = "This is text$delmited text$and more text"
        l = [["This is text"], ["delmited text"], ["and more text"]]
        assert l == parse.split_by_delim(data=s, delim=["$", "#"], quotechar=None)

    def test_no_middle(self):
        s = "Text 1$$Text 2"
        l = ["Text 1", "", "Text 2"]
        assert l == parse.split_by_delim(data=s, delim=["$"], quotechar=None)

    def test_no_end(self):
        s = "Text 1$"
        l = ["Text 1", ""]
        assert l == parse.split_by_delim(data=s, delim=["$"], quotechar=None)


    def test_no_middle_second_level(self):
        s = "This is text$with delimited text##inside of delimited text$other text"
        l = [["This is text"], ["with delimited text", "", "inside of delimited text"], ["other text"]]
        assert l == parse.split_by_delim(data=s, delim=["$", "#"], quotechar=None)

    def test_no_end_second_level(self):
        s = "This is text$with delimited text#$other text"
        l = [["This is text"], ["with delimited text", ""], ["other text"]]
        assert l == parse.split_by_delim(data=s, delim=["$", "#"], quotechar=None)

    def test_multilevel_empty_final(self):
        s = "This is text$with delimited text##inside of delimited text$"
        l = [["This is text"], ["with delimited text", "", "inside of delimited text"], []]
        assert l == parse.split_by_delim(data=s, delim=["$", "#"], quotechar=None)