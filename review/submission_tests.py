""" This file contains methods for getting and returning unit test results for
    a user's submissions.
"""

def get_results():
    """loads a text file containing test results (in a specific
    format) and processes them.

    This method does not validate the format but assumes the lecturer
    has put their unit test overview in the right format.  This test
    allows lecturers to choose which parameters they would like
    to include and works with what it gets.  If lecturers have excluded certain
    parameters their keys will still be there but the values will be None. 
  
    Returns a dictionary containing test overview parameters and their values

    get_results() -> dict(str:str)

    """
    # TODO: Connect to testing environment.
    results_file = open("ENKIDU_test_overview.txt", 'rU') #open file for reading
    results_file_lines = [] #create a list for lines in file
    for line in results_file:
        results_file_lines.append(line.strip())
    k = results_file_lines
    test_overview = {}
    #if test parameter in list, then add it to dictionary with relevant value
    if "Amount Tests:" in k:
        amount_tests = k[k.index("Amount Tests:") + 1]
        test_overview["amount_tests"] = amount_tests
    if "Amount Failures:" in k:
        amount_failures = k[k.index("Amount Failures:") + 1]
        test_overview["amount_failures"] = amount_failures
    if "Final Result:" in k:
        final_result = k[k.index("Final Result:") + 1]
        test_overview["final_result"] = final_result
    if "Total Time:" in k:
        total_time = k[k.index("Total Time:") + 1]
        test_overview["total_time"] = total_time
    if "Errors:" in k:
        errors = k[k.index("Errors:") + 1]
        test_overview["errors"] = errors
    return test_overview