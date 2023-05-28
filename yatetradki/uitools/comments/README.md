# comments

This is a tool that helps working with Google Docs comments.

## GPT

One usage is to automatically add GPT explanations to marked words in a document. For each comment GPT is asked to provide translation, explanation, synonyms/antonyms for the selected word in the sentense.

+ user adds a comment
- run with flock (/tmp/comments.lock), persistent rate limit (for GPT)
+ export document as HTML with comments (need cookies)
- parse document to make a list of comments. they contain
  - id (user later for API)
  - selection (all the words that are marked)
  - context (the sentense)
  - comment (the comment text)
- for c in unprocessed: those that don't have '<GPT>' in the comment text
  - query GPT, get response
  - add response to comment text
  - update comment, use Google API SDK


