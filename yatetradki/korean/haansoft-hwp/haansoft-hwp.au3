#include <Constants.au3>
#include <AutoItConstants.au3>
#include <FileConstants.au3>
#include <MsgBoxConstants.au3>
#include <WinAPIFiles.au3>

; Positions on the screen
$TITLE_X = 90
$TITLE_Y = 45
$LIST_1_X = $TITLE_X
$LIST_1_Y = $TITLE_Y + 20
$LIST_2_X = $TITLE_X
$LIST_2_Y = $LIST_1_Y + 15
$ARTICLE_X = $TITLE_X + 200
$ARTICLE_Y = $LIST_2_Y

Sleep(3000)

; Index format:
; 4bytes - entry offset
; 4bytes - title length
; 4bytes - article length
$hFileData = FileOpen("z:\korean_research\temp\haansoft-hwp-koko.txt", $FO_APPEND)
$hFileIndex = FileOpen("z:\korean_research\temp\haansoft-hwp-koko.index", $FO_APPEND)
$Offset = Int(FileGetPos($hFileData), $NUMBER_32BIT)

$OldArticle = ""
$OldSeenTimes = 0
$OldSeenTimesMax = 10

;~ GrabEntry($LIST_1_X, $LIST_1_Y)
For $i = 0 To 100000
	$Stop = GrabEntry($LIST_2_X, $LIST_2_Y)
	If $Stop > 0 Then ExitLoop
Next
;~ MsgBox($MB_SYSTEMMODAL, "", "Contents of the file:" & @CRLF & Binary(42))

FileClose($hFileData)
FileClose($hFileIndex)


Func GrabEntry($LIST_X, $LIST_Y)
	MouseClick("left", $LIST_X, $LIST_Y)
	MouseClick("left", $TITLE_X, $TITLE_Y)
	Send("{CTRLDOWN}a{CTRLUP}{CTRLDOWN}c{CTRLUP}")
	$Title = ClipGet()

	MouseClick("left", $ARTICLE_X, $ARTICLE_Y)
	Send("{CTRLDOWN}a{CTRLUP}{CTRLDOWN}c{CTRLUP}")
	$Article = ClipGet()

	FileWrite($hFileData, $Title)
	$TitleOffset = Int(FileGetPos($hFileData), $NUMBER_32BIT)
	$TitleLen = $TitleOffset - $Offset

	FileWrite($hFileData, $Article)
	$ArticleOffset = Int(FileGetPos($hFileData), $NUMBER_32BIT)
	$ArticleLen = $ArticleOffset - $TitleOffset

	FileWrite($hFileIndex, Binary($Offset))
	FileWrite($hFileIndex, Binary($TitleLen))
	FileWrite($hFileIndex, Binary($ArticleLen))

	$Offset = $ArticleOffset
;~ 	$Offset + StringLen($Title) + StringLen($Article)

	MouseClick("left", $LIST_X, $LIST_Y)
	Send("{down}")

	If $Article = $OldArticle Then
		$OldSeenTimes = $OldSeenTimes + 1
		If $OldSeenTimes >= $OldSeenTimesMax Then
			Return 1
		EndIf
	Else
		$OldArticle = $Article
		$OldSeenTimes = 0
		Return 0
	EndIf
EndFunc

;~MsgBox($MB_SYSTEMMODAL, "", "Contents of the file:" & @CRLF & FileRead($Path))
;~ (0, "title", $Text)
