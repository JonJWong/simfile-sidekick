grammar search;

CHAR: ~[\b\r\n\t\f];

search_statement: song_title |
                  song_title (' ' tag_statement)+ |
                  tag_statement (' ' tag_statement)*;
                  
song_title: value;
tag_statement: '-' tag ':' value;
tag : 'title' | 'subtitle' | 'artist' | 'stepartist' | 'rating' | 'bpm';
value: CHAR+ (' '* CHAR+)*;

// TODO: support range search

// proposed grammar:
// TAG:VALUE+
// TAG:VALUE-
// TAG:VALUE-VALUE

// TODO: support 'totalstream' and 'totalbreak', 'density'
// (total stream, total break, density are virtually useless without range search)
