#!/usr/bin/python

"""Compress and upload a single item from a session
for use in 'emergency' cases only"""

import sys, os

if __name__=='__main__':
    if not len(sys.argv) == 3:
        print "Usage upload_item.py <raw item xml> <final dir>"
        print "  eg. upload_item.py D:\\recordings\\Spkr1_1121_Session1\\Session1_12\\1_1121_12_001.xml D:\\final"
        print "Compress and upload a single item"
        exit()

    from datahandling import RecordedItem
    import config
    config.configinit()
    
    item_xml = sys.argv[1]
    finaldir = sys.argv[2]

    (rawdir, basename) = os.path.split(item_xml)
    (item_id, ext) = os.path.splitext(basename)
    
    host = config.config('HOST_FINAL', 'austalk.edu.au')
    logfile = "upload_item_log.txt"
    
    print "Item is ", item_id
    
    raw_item = RecordedItem(rawdir, item_id)
    final_item_dir = os.path.join(finaldir, raw_item.get_dir_name())
  
    # first check to see whether we have a compressed version
    cmp_item = RecordedItem(final_item_dir, item_id)
    print "Validating files in compressed version of item in", final_item_dir
    (errors, warnings) = cmp_item.validate_files()
    
    if len(errors) > 0:
        print "Errors in compressed version: "
        for e in errors:
            print "\t", e
    
    if len(warnings) > 0:
        print "Warnings for compressed version: "
        for w in warnings:
            print "\t", w
    
    # if there are errors, we need to re-compress
    if len(errors) > 0 or len(warnings) > 0:
        print "Recompressing and uploading raw item from", rawdir

        (success, files, error_msgs) = raw_item.convert_video_and_upload(finaldir, host, logfile)
        if not success:
            print "Errors in compress/upload:"
            for m in error_msgs:
                print "\t", m
        else:
            print "Upload successful"
    else:
        # we can just upload the compressed version
        print "No errors or warnings for compressed version"
        print "Uploading compressed item from", finaldir
        (success, error_msgs) = cmp_item.upload_files(host, logfile)
        if not success:
            print "Errors uploading data:"
            for m in error_msgs:
                print "\t", m
        else:
            print "upload successful"
            
            
            