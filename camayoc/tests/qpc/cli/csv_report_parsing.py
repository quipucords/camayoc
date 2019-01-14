# coding=utf-8
"""Helper functions for parsing csv reports"""

import csv


def normalize_csv_report(f, header_range, header_lines, report_type='summary'):
    """ Extracts and normalizes csv report to match the returned JSON report.

    :param f: A file object for the csv
    :param header_range: An int specifing the range that the head extends into
        the csv file.
    :param header_lines: A list of tuples containg the index pairs for the
        lines to be used as the key/value pairs of each header info dictionary
        (ex: [(0,1), (3,4)] ).
    :param report_type: A string that defines what type of report object to
        return, 'summary' or 'detail'. Defaults to 'summary'.
    """
    # First grab the header information from the file object.
    report_headers = [f.readline() for _ in range(header_range)]
    # Next, extract header information into a list of dictonaries (1 dictionary
    # per header set)
    header_info = extract_key_value_lines(report_headers,
                                          header_lines)
    # Now that we extracted the report information we can use CSV reader to
    # read the system fingerprints information
    reader = csv.DictReader(f)
    if report_type == 'summary':
        report = normalize_summary_report(header_info, reader)
    else:
        report = normalize_detail_report(header_info, reader)
    return report


def normalize_summary_report(header_info, reader):
    """Takes information from report_info dict, and reader and returns a
    summary report"""
    report_info = header_info[0]
    report = {
        'report_id': report_info['report_id'],
        'report_type': report_info['report_type'],
        'report_version': report_info['report_version'],
        'report_platform_id': report_info['report_platform_id'],
        'system_fingerprints': [row for row in reader],
    }
    return report


def normalize_detail_report(header_info, reader):
    """Takes information from report_info dict, and reader and returns a
    detail format report"""
    # The first dictionary grabbed contains the report info
    report_info = header_info[0]
    # The second contains the source header info
    source_info = header_info[1]
    report = {
        'id': report_info['report_id'],
        'report_type': report_info['report_type'],
        'sources': [{
            'facts': [row for row in reader],
            'server_id': source_info['server_identifier'],
            'source_name': source_info['source_name'],
            'source_type': source_info['source_type'],
        }],
    }
    return report


def extract_key_value_lines(input_lines, line_pairs, delim=','):
    """Extracts several line pairs into dictionaries, and returns a list of
    all of them

    :param input_lines: a list of csv line strings.
    :param line_pairs: A list of tuples containg the index pairs for the lines
        to be used as the key/value pairs of each dictionary
        (ex: [(0,1), (3,4)] ).
    :param delim: the delimiter to split the lines with (defaults to ',').
    """
    return [zip_line_pairs(input_lines, key_ind, value_ind, delim=delim)
            for (key_ind, value_ind) in line_pairs]


def zip_line_pairs(input_lines, key_ind, value_ind, delim=','):
    """Takes a list of csv strings, and zips 2 of them into a dictionary.

    :param input_lines: a list of csv lines
    :param key_ind: the index value for which line in ``input_lines`` should be
        used for the keys of the dictionary.
    :param value_ind: the index value for which line in ``input_lines`` should
        be used for the values of the dictionary.
    :param delim: the delimiter to split the lines with (defaults to ',').
    """
    header_keys = input_lines[key_ind].strip().split(delim)
    header_values = input_lines[value_ind].strip().split(delim)

    # Dynamically Pull the header items into a dictionary.
    paired_info = dict(map(lambda key, value:
                           [key.lower().replace(' ', '_'), value],
                           header_keys,
                           header_values))
    return paired_info
