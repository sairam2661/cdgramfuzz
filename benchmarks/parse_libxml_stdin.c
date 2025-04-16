#include <stdio.h>
#include <libxml/parser.h>
#include <libxml/tree.h>

int main(int argc, char **argv) {
    xmlDocPtr doc;
    
    // Parse XML from stdin
    doc = xmlReadFd(0, "stdin", NULL, 0);
    
    // Free the document if parsing was successful
    if (doc != NULL) {
        xmlFreeDoc(doc);
    }
    
    // Cleanup parser
    xmlCleanupParser();
    
    return 0;
}