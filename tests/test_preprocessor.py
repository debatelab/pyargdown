
import pytest
from textwrap import dedent

from pyargdown.parser.preprocessor import (
    RemoveCommentsHandler,
    RemoveWhitespaceHandler,
    CollapseLinesHandler,
    RemoveTrailingWhitespaceHandler,
    Preprocessor,
    ArgumentBlock,
    ArgumentMapBlock,
    remove_html_comments,
    remove_js_comments,
)


@pytest.fixture
def argdown_text_1():
    return dedent("""
    # Test argument map

    <Test argument>: Test 
        PCS.

      /*Now the reco:*/
      (1) Premise runs
      over two lines.
      // Let's draw a conclusion
      --
      Test inference
      --
      (2) Conclusion.
                  
    """)

@pytest.fixture
def argdown_text_2():
    return dedent("""
    /*
    Comment: And here's an argument map:
    */
    [Root]: Root
        spans
        multiple
        lines.
        <+ [Child]: Child
            spans
            multiple
            lines. // And here's a comment
        <- [Child]: Child.
                  /* And here's a comment */
                  /* And here's 
                  another comment */
    [Root2]: Root2.
    """)

@pytest.fixture
def funny_argument_blocks():
    return [
        dedent("""
        <Argument>: Argument

        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument // comment
        // comment

        //comment
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument /* comment 
               
        */

               
        /*
        A mean comment!       
               
        */
        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument

        // comment
        (1) Premise.
        // comment
        ----
        (2) Conclusion.                          
        """).strip(),
    ]

@pytest.fixture
def argument_blocks_with_reasons():
    return [
        dedent("""
        <Argument>: Argument

        (1) Premise.
            <+ Evidence.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument

        (1) Premise.
            <+ Evidence.
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument 

        (1) Premise.
        [Evidence]
        ----
        (2) Conclusion.                          
        """).strip(),
        dedent("""
        <Argument>: Argument 
        (1) Premise.
        ----
        (2) Conclusion.
          >< Contradiction.                      
        """).strip(),
        dedent("""
        <Argument>: Argument

        (1) Premise.
          + [E1]
            - [E2]
        ----
        (2) Conclusion.                          
        """).strip(),
    ]


@pytest.fixture
def argument_blocks_with_multiple_args():
    return [
        dedent("""
        <Argument1>: Argument

        (1) Premise.
        ----
        (2) Conclusion.                          

               
        <Argument2>: Argument

        (1) Premise.
        ----
        (2) Conclusion.                          
        """).strip(),
    ]


def test_remove_comments(argdown_text_2, funny_argument_blocks):
    result = remove_js_comments(argdown_text_2)
    print(argdown_text_2)
    print("\n--------\n")
    print(result)
    assert "/*" not in result
    assert "*/" not in result
    argdown_text_2 = argdown_text_2.replace("/*", "<!--").replace("*/", "-->")
    assert "<!--" in argdown_text_2
    assert "-->" in argdown_text_2
    result = remove_html_comments(argdown_text_2)
    print(result)
    assert "<!--" not in result
    assert "-->" not in result

    for block in funny_argument_blocks:
        cleaned = remove_js_comments(block)
        cleaned = remove_html_comments(cleaned)
        print("\n--------")
        print(cleaned)
        assert "/*" not in cleaned
        assert "*/" not in cleaned
        assert "<!--" not in cleaned
        assert "-->" not in cleaned

def test_remove_comments_handler(argdown_text_1, argdown_text_2):
    handler = RemoveCommentsHandler()
    result_1 = handler(argdown_text_1)
    print(result_1)
    assert "/*Now the reco:*/" not in result_1
    assert "// Let's draw a conclusion" not in result_1

    result_2 = handler(argdown_text_2)
    print(result_2)
    #assert dedent(
    #    """
    #    /*
    #    Comment: And here's an argument map:
    #    */"""
    #) not in result_2
    assert "/* And here's a comment */" not in result_2
    #assert "/* And here's \n                  another comment */" not in result_2

def test_remove_whitespace_handler(argdown_text_1):
    handler = RemoveWhitespaceHandler()
    result = handler(argdown_text_1)
    print(result)
    assert not any([line.startswith(" ") for line in result.split("\n")])
    assert all(line.strip() in result for line in argdown_text_1.split("\n"))

def test_collapse_lines_handler(argdown_text_1, argdown_text_2):
    handler = CollapseLinesHandler()
    result_1 = handler(argdown_text_1)
    print(result_1)
    assert "Test PCS." in result_1
    assert len(result_1.split("\n")) == 11

    result_2 = handler(argdown_text_2)
    print(result_2)
    assert "/* Comment: And here's an argument map: */" in result_2
    assert "Root spans multiple lines." in result_2
    assert "<+ [Child]: Child spans multiple lines. // And here's a comment" in result_2
    assert "<- [Child]: Child. /* And here's a comment */ /* And here's another comment */" in result_2

def test_collapse_lines_with_reasons(argument_blocks_with_reasons):
    handler = CollapseLinesHandler()
    for block in argument_blocks_with_reasons:
        print("\n========\n")
        print(f"{block}\n\n")
        result = handler(block)
        print(result)
        assert block == result

def test_split_blocks(argdown_text_1, argdown_text_2):
    text = argdown_text_1 + "\n\n" + argdown_text_1 + "\n\n" + argdown_text_2
    print(text)
    text = remove_js_comments(text)
    text = remove_html_comments(text)
    print("====\n")
    print(text)
    blocks = Preprocessor.split_blocks(text)
    for block in blocks:
        print(f"--- block {type(block)} ---")
        print(block)
    assert len(blocks) == 5
    assert isinstance(blocks[0], ArgumentMapBlock)
    assert isinstance(blocks[1], ArgumentBlock)
    assert isinstance(blocks[2], ArgumentMapBlock)
    assert isinstance(blocks[3], ArgumentBlock)
    assert isinstance(blocks[4], ArgumentMapBlock)


def test_split_blocks2(argument_blocks_with_multiple_args):
    for text in argument_blocks_with_multiple_args:
        print(text)
        text = remove_js_comments(text)
        text = remove_html_comments(text)
        print("====\n")
        print(text)
        blocks = Preprocessor.split_blocks(text)
        for block in blocks:
            print(f"--- block {type(block)} ---")
            print(block)
        assert len(blocks) > 1
        assert all(isinstance(block, ArgumentBlock) for block in blocks)

def test_parse_argdown(argdown_text_1, argdown_text_2):
    
    preprocessor = Preprocessor()
    preprocessor.add_handler(
        RemoveCommentsHandler()
    ).add_handler(
        RemoveWhitespaceHandler()
    ).add_handler(
        CollapseLinesHandler()
    ).add_handler(
        RemoveCommentsHandler()
    ).add_handler(
        RemoveTrailingWhitespaceHandler()
    )
    
    argdown_text_1 = remove_js_comments(argdown_text_1)
    argdown_text_1 = remove_html_comments(argdown_text_1)
    block = preprocessor.split_blocks(argdown_text_1)[1]
    print(type(block))
    print(block)
    result_1 = preprocessor.process(block)
    print(f"{type(result_1)}:\n{result_1}")
    assert result_1 == (
        "<Test argument>: Test PCS.\n\n"
        "(1) Premise runs over two lines.\n"
        "--\n"
        "Test inference\n"
        "--\n"
        "(2) Conclusion."
    )

    print("\n\n\n")

    argdown_text_2 = remove_js_comments(argdown_text_2)
    argdown_text_2 = remove_html_comments(argdown_text_2)
    block = preprocessor.split_blocks(argdown_text_2)[0]
    result_2 = preprocessor.process(block)
    print(block)
    print(result_2)
    assert result_2 == (
        "\n"
        "[Root]: Root spans multiple lines.\n"
        "    <+ [Child]: Child spans multiple lines.\n"
        "    <- [Child]: Child.\n"
        "[Root2]: Root2.\n"
    )
