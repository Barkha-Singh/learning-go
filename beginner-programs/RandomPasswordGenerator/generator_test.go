package main

import (
    "strings"
    "testing"
    "unicode"
)


func TestGeneratePassword(t *testing.T) {
	password := generatePassword(15)

	// Check length
	if len(password) != 15 {
		t.Errorf("expected password length 15, got %d", len(password))
	}

	// Check at least one digit
	if !containsDigit(password) {
		t.Errorf("expected at least one digit in password, got %s", password)
	}

	// Check at least one special character
	if !containsSpecialCharacter(password) {
		t.Errorf("expected at least one special character in password, got %s", password)
	}
}

func containsDigit(password string) bool {
	for _, c := range password {
		if unicode.IsDigit(c) {
			return true
		}
	}
	return false
}

func containsSpecialCharacter(password string) bool {
	specials := "~=+%^*/()[]{}/!@#$?|"
	for _, c := range password {
		if strings.ContainsRune(specials, c) {
			return true
		}
	}
	return false
}
