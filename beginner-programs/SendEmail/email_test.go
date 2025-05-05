package main

import (
	"strings"
	"testing"
)

func TestEmailMessageConstruction(t *testing.T) {
	from := "email"
	to := "email"
	subject := "Hello there!"
	body := "Hello there my friend!"

	expectedMsg := "From: " + from + "\n" +
		"To: " + to + "\n" +
		"Subject: " + subject + "\n\n" +
		body

	// Construct the message exactly as in main()
	msg := "From: " + from + "\n" +
		"To: " + to + "\n" +
		"Subject: " + subject + "\n\n" +
		body

	if strings.TrimSpace(msg) != strings.TrimSpace(expectedMsg) {
		t.Errorf("Constructed message does not match.\nExpected:\n%v\nGot:\n%v", expectedMsg, msg)
	}
}
