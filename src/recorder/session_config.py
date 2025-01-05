


from Domain import Component, Session

#        id,    name,              duration, layout,     prompt directory,        sync, prompt map file, short name
Component(11,   u'Calibration',             600, u'Prompts', u'Protocol-3D-Calibration', 1, u'Protocol-3D-Calibration.map', 'calibration')
Component(1,    u'Yes/No Opening',          180, u'YesNo',   u'Protocol-OpeningYesNo-Session1', 0, u'Protocol-OpeningYesNo-Session1.map', 'yes-no-opening-1')
Component(3,    u'Story',                   300, u'Prompts', u'Protocol-Story', 1, u'Protocol-Story.map', 'story')
Component(4,    u'Re-told Story',           600, u'Prompts', u'Protocol-Retold-Story', 0, u'Protocol-Retold-Story.map', 're-told-story')
Component(5,    u'Digits',                  300, u'Prompts', u'Protocol-Digits', 1, u'Protocol-Digits.map', 'digits')
Component(9,    u'Yes/No Closing',          120, u'YesNo',   u'Protocol-ClosingYesNo', 0, u'Protocol-ClosingYesNo.map', 'yes-no-closing')
#
Component(21,   u'Yes/No Opening',          180, u'YesNo',   u'Protocol-OpeningYesNo-Session2', 0, u'Protocol-OpeningYesNo-Session2.map', 'yes-no-opening-2')




Component(2,    u'Words - Session 1',       600, u'Prompts', u'Protocol-Words_Session1', 1, u'Protocol-Words_Session1.map', 'words-1')
Component(22,   u'Words - Session 2',       600, u'Prompts', u'Protocol-Words_Session2', 1, u'Protocol-Words_Session2.map', 'words-2')
Component(32,   u'Words - Session 3',       600, u'Prompts', u'Protocol-Words_Session3', 1, u'Protocol-Words_Session3.map', 'words-3')

# corrections made to prompts for words
# replace duplicate heen with heed in Session 2
# in all sessions, modify the prompt for 'hooll sounds like tool' to 'hooll sounds like full' 
# note that earlier prompts have been modified to 'hool sounds like tool' (one l in hool)
# to better reflect the pronunciation
Component(43,   u'Words - Session 1 (v2)',  600, u'Prompts', u'Protocol-Words_Session1v2', 1, u'Protocol-Words_Session1v2.map', 'words-1-2')
Component(23,   u'Words - Session 2 (v2)',  600, u'Prompts', u'Protocol-Words_Session2v2', 1, u'Protocol-Words_Session2v2.map', 'words-2-2')
Component(33,   u'Words - Session 3 (v2)',  600, u'Prompts', u'Protocol-Words_Session3v2', 1, u'Protocol-Words_Session3v2.map', 'words-3-2')



Component(7,    u'Interview',               900, u'Prompts', u'Protocol-Interview', 0, u'Protocol-Interview.map', 'interview')
Component(16,   u'Sentences Session 2',     480, u'Prompts', u'Protocol-Sentences-Session2', 1, u'Protocol-Sentences-Session2.map', 'sentences')
#
Component(31,   u'Yes/No Opening',          180, u'YesNo',   u'Protocol-OpeningYesNo-Session3', 0, u'Protocol-OpeningYesNo-Session3.map', 'yes-no-opening-3')
Component(8,    u'Map Task 1',              1200, u'MapTask', u'Protocol-MapTask', 0, u'Protocol-MapTask.map', 'maptask-1')
#
Component(10,   u'Map Task 2',              1200, u'MapTask', u'Protocol-MapTask', 0, u'Protocol-MapTask.map', 'maptask-2')
Component(12,   u'Conversation',            200, u'Prompts', u'Protocol-Conversation', 1, u'Protocol-Conversation.map', 'conversation')

# legacy components - used in earlier versions
Component(6,     u'Sentences Session 2',    480, u'Prompts', u'Protocol-Sentences-Session2', 1, u'Protocol-Sentences-Session2.map', 'sentences')
# this is component 16 with re-ordered sentences which was originally recorded in the wrong order
Component(17,    u'Sentences Session 2 (early)',   480, u'Prompts', u'Protocol-Sentences-Session2', 1, u'Protocol-Sentences-Session2.map', 'sentences-e')
##This one is a problem as we re-used id 12 for Conversation so some older data has been wrongly labelled as conversation
#Component(12,    u'Words - Session 1',     600, u'Prompts', u'Protocol-Words_Session1', 1, u'Protocol-Words_Session1.map')
Component(13,    u'Words - Session 2',      600, u'Prompts', u'Protocol-Words_Session2', 1, u'Protocol-Words_Session2.map', 'words-2')
Component(14,    u'Words - Session 3',      600, u'Prompts', u'Protocol-Words_Session3', 1, u'Protocol-Words_Session3.map', 'words-3')


# new components for Emotional speech

Component(18,   u'Emotion-Videos1',         1200, u'Prompts',   u'Protocol-emotions-videos1', 1, u'Protocol-emotions-videos1.map', 'Emotion-Videos')
Component(19,   u'Emotion-Images1',         600, u'Prompts',   u'Protocol-emotions-images1', 1, u'Protocol-emotions-images1.map', 'Emotion-Images')
Component(98,   u'Emotion-Videos2',         1200, u'Prompts',   u'Protocol-emotions-videos2', 1, u'Protocol-emotions-videos2.map', 'Emotion-Videos')
Component(99,   u'Emotion-Images2',         600, u'Prompts',   u'Protocol-emotions-images2', 1, u'Protocol-emotions-images2.map', 'Emotion-Images')
Component(108,   u'Emotion-Videos3',        1200, u'Prompts',   u'Protocol-emotions-videos3', 1, u'Protocol-emotions-videos3.map', 'Emotion-Videos')
Component(109,   u'Emotion-Images3',        600, u'Prompts',   u'Protocol-emotions-images3', 1, u'Protocol-emotions-images3.map', 'Emotion-Images')
Component(70,    u'InterviewEmo1',           900, u'Prompts', u'Protocol-Interview', 0, u'Protocol-Interview.map', 'interview1')
Component(71,    u'InterviewEmo2',           900, u'Prompts', u'Protocol-Interview', 0, u'Protocol-Interview.map', 'interview2')


### Sessions
#       id, name          , list of component ids
Session(1, "Session 1",   [11, 1, 43, 3, 4, 5, 9])
Session(2, "Session 2",   [21, 23, 7, 5, 16, 9])
Session(3, "Session 3.1", [31, 33, 8])
Session(4, "Session 3.2", [10, 12, 33, 9])

# new sessions for emotional speech 
Session(5, "Session 1 Emotion",   [11, 1, 43, 19, 18, 5, 9])
Session(6, "Session 2 Emotion",   [21, 23, 99, 98, 5, 16, 9])
Session(7, "Session 3 Emotion",   [31, 33, 109, 108, 70, 71, 9])

sessions = Session.GetInstances()
components = Component.GetInstances()
