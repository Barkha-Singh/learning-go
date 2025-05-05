package email

import (
        "errors"
        "testing"

        "github.com/golang/mock/gomock"
        mock_email "github.com/your/module/path/email/mocks" // update to real module path
)

// TestIsValid verifies the behaviour of IsValid for a variety of inputs.
func TestIsValid(t *testing.T) {
        t.Parallel()

        tests := []struct {
                name   string
                input  string
                expect bool
        }{
                {
                        name:   "empty string",
                        input:  "",
                        expect: false,
                },
                {
                        name:   "missing at-sign",
                        input:  "plainaddress",
                        expect: false,
                },
                {
                        name:   "missing local part",
                        input:  "@no-local-part.com",
                        expect: false,
                },
                {
                        name:   "simple valid email",
                        input:  "email@example.com",
                        expect: true,
                },
                {
                        name:   "sub-domain",
                        input:  "email@sub.example.com",
                        expect: true,
                },
                {
                        name:   "dotted local part",
                        input:  "first.last@example.co.uk",
                        expect: true,
                },
        }

        for _, tt := range tests {
                tt := tt // capture range variable
                t.Run(tt.name, func(t *testing.T) {
                        t.Parallel()

                        got := IsValid(tt.input)
                        if got != tt.expect {
                                t.Fatalf("IsValid(%q) = %v, want %v", tt.input, got, tt.expect)
                        }
                })
        }
}

// TestComposeAndSend exercises the high-level ComposeAndSend helper.
// It demonstrates success, validation failure, and sender error propagation.
func TestComposeAndSend(t *testing.T) {
        t.Parallel()

        ctrl := gomock.NewController(t)
        defer ctrl.Finish()

        mockSender := mock_email.NewMockSender(ctrl)

        validationErr := errors.New("invalid email address")
        sendErr := errors.New("SMTP failure")

        tests := []struct {
                name          string
                to            string
                subject       string
                body          string
                mockExpect    func()
                wantErr       error
        }{
                {
                        name:    "happy path",
                        to:      "user@example.com",
                        subject: "Greetings",
                        body:    "Hello, world!",
                        mockExpect: func() {
                                mockSender.EXPECT().
                                        Send("user@example.com", "Greetings", "Hello, world!").
                                        Return(nil)
                        },
                        wantErr: nil,
                },
                {
                        name:    "invalid recipient",
                        to:      "not-an-email",
                        subject: "Hi",
                        body:    "Body",
                        mockExpect: func() {
                                // ComposeAndSend should validate and return before hitting Send.
                        },
                        wantErr: validationErr,
                },
                {
                        name:    "sender error",
                        to:      "user@example.com",
                        subject: "Oops",
                        body:    "Something went wrong",
                        mockExpect: func() {
                                mockSender.EXPECT().
                                        Send("user@example.com", "Oops", "Something went wrong").
                                        Return(sendErr)
                        },
                        wantErr: sendErr,
                },
        }

        for _, tt := range tests {
                tt := tt
                t.Run(tt.name, func(t *testing.T) {
                        // Arrange
                        if tt.mockExpect != nil {
                                tt.mockExpect()
                        }

                        // Act
                        err := ComposeAndSend(mockSender, tt.to, tt.subject, tt.body)

                        // Assert
                        if !errors.Is(err, tt.wantErr) {
                                t.Fatalf("ComposeAndSend() error = %v, want %v", err, tt.wantErr)
                        }
                })
        }
}