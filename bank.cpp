#include <iostream>
#include <fstream>
#include <vector>
#include <string>
using namespace std;

class BankAccount {
private:
    string accountHolderName;
    int accountNumber;
    double balance;

public:
    BankAccount() {} // Required for file reading

    BankAccount(string name, int accNum, double initialDeposit)
        : accountHolderName(name), accountNumber(accNum), balance(initialDeposit) {}

    void displayAccount() const {
        cout << "\n--- Account Details ---\n";
        cout << "Account Holder: " << accountHolderName << endl;
        cout << "Account Number: " << accountNumber << endl;
        cout << "Balance: $" << balance << endl;
    }

    void deposit(double amount) {
        if (amount > 0) {
            balance += amount;
            cout << "Deposited $" << amount << " successfully.\n";
        } else {
            cout << "Invalid deposit amount.\n";
        }
    }

    void withdraw(double amount) {
        if (amount > 0 && amount <= balance) {
            balance -= amount;
            cout << "Withdrew $" << amount << " successfully.\n";
        } else {
            cout << "Invalid or insufficient funds.\n";
        }
    }

    int getAccountNumber() const {
        return accountNumber;
    }

    string getName() const {
        return accountHolderName;
    }

    double getBalance() const {
        return balance;
    }

    void setBalance(double b) {
        balance = b;
    }

    void save(ofstream& out) const {
        out << accountHolderName << '\n'
            << accountNumber << '\n'
            << balance << '\n';
    }

    void load(ifstream& in) {
        getline(in, accountHolderName);
        in >> accountNumber >> balance;
        in.ignore(); // skip the newline
    }
};

// Global variables
vector<BankAccount> accounts;
int nextAccountNumber = 1001;
const string DATA_FILE = "accounts.dat";

// Function prototypes
void createAccount();
void accessAccount();
void saveAccountsToFile();
void loadAccountsFromFile();

int main() {
    loadAccountsFromFile();

    int choice;
    do {
        cout << "\n=== Online Banking System ===\n";
        cout << "1. Create Account\n";
        cout << "2. Access Account\n";
        cout << "3. Exit\n";
        cout << "Enter your choice: ";
        cin >> choice;

        switch (choice) {
            case 1:
                createAccount();
                break;
            case 2:
                accessAccount();
                break;
            case 3:
                saveAccountsToFile();
                cout << "Thank you for using the Online Banking System.\n";
                break;
            default:
                cout << "Invalid choice. Please try again.\n";
        }
    } while (choice != 3);

    return 0;
}

void createAccount() {
    string name;
    double initialDeposit;

    cin.ignore(); // clear input buffer
    cout << "Enter account holder's name: ";
    getline(cin, name);
    cout << "Enter initial deposit amount: ";
    cin >> initialDeposit;

    BankAccount newAccount(name, nextAccountNumber++, initialDeposit);
    accounts.push_back(newAccount);
    saveAccountsToFile();

    cout << "Account created successfully! Your account number is: " << newAccount.getAccountNumber() << endl;
}

void accessAccount() {
    int accNum;
    cout << "Enter account number: ";
    cin >> accNum;

    bool found = false;
    for (auto& acc : accounts) {
        if (acc.getAccountNumber() == accNum) {
            found = true;
            int option;
            do {
                cout << "\n--- Account Menu ---\n";
                cout << "1. View Account\n";
                cout << "2. Deposit\n";
                cout << "3. Withdraw\n";
                cout << "4. Back to Main Menu\n";
                cout << "Enter option: ";
                cin >> option;

                switch (option) {
                    case 1:
                        acc.displayAccount();
                        break;
                    case 2: {
                        double amount;
                        cout << "Enter deposit amount: ";
                        cin >> amount;
                        acc.deposit(amount);
                        saveAccountsToFile();
                        break;
                    }
                    case 3: {
                        double amount;
                        cout << "Enter withdrawal amount: ";
                        cin >> amount;
                        acc.withdraw(amount);
                        saveAccountsToFile();
                        break;
                    }
                    case 4:
                        cout << "Returning to main menu...\n";
                        break;
                    default:
                        cout << "Invalid option.\n";
                }
            } while (option != 4);
            break;
        }
    }

    if (!found) {
        cout << "Account not found.\n";
    }
}

void saveAccountsToFile() {
    ofstream out(DATA_FILE);
    if (!out) {
        cerr << "Error saving to file.\n";
        return;
    }

    out << accounts.size() << '\n';
    out << nextAccountNumber << '\n';
    for (const auto& acc : accounts) {
        acc.save(out);
    }
    out.close();
}

void loadAccountsFromFile() {
    ifstream in(DATA_FILE);
    if (!in) return;

    size_t count;
    in >> count;
    in >> nextAccountNumber;
    in.ignore(); // skip the newline

    accounts.clear();
    for (size_t i = 0; i < count; ++i) {
        BankAccount acc;
        acc.load(in);
        accounts.push_back(acc);
    }

    in.close();
}
