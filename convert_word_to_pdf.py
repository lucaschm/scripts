import os
import win32com.client

def convert_doc_to_pdf(doc_path, pdf_path):
    try:
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(doc_path)
        doc.SaveAs(pdf_path, FileFormat=17)  # 17 is the code for PDF format
        doc.Close()
        word.Quit()
    except Exception as e:
        print(f"Failed to convert {doc_path} to PDF. Error: {e}")
        return False
    return True

def count_files_to_be_converted(directory):
    word_file_count = 0
    existing_pdf_count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.doc', '.docx')):
                doc_file = os.path.join(root, file)
                print(f"Word document found: {doc_file}")
                word_file_count += 1
                pdf_file = os.path.splitext(doc_file)[0] + ".pdf"
                if os.path.exists(pdf_file):
                    existing_pdf_count += 1
                    print(f"Existing PDF: {pdf_file}")
    return word_file_count, existing_pdf_count

def convert_all_docs_in_directory(directory, overwrite=False):
    converted_files = []
    corrupted_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.doc', '.docx')):
                doc_file = os.path.join(root, file)
                pdf_file = os.path.splitext(doc_file)[0] + ".pdf"
                if not os.path.exists(pdf_file) or overwrite:
                    if convert_doc_to_pdf(doc_file, pdf_file):
                        print(f"Converted: {doc_file}")
                        converted_files.append(doc_file)
                    else:
                        corrupted_files += 1
                else:
                    print(f"Skipped (PDF already exists): {pdf_file}")
    return converted_files, corrupted_files

def main():
    print("This script will convert all .doc and .docx files in the specified directory and its subdirectories to PDFs.")
    
    directory = input("Please enter the path to the root directory containing Microsoft Word files: ").strip()
    
    while not os.path.isdir(directory):
        print("The provided path is not a valid directory. Please try again.")
        directory = input("Please enter the path to the root directory containing Microsoft Word files: ").strip()
    
    print("\nCalculating the number of files to be converted and existing PDF files...")
    word_file_count, existing_pdf_count = count_files_to_be_converted(directory)


    
    print(f"\nThis is the Target directory: {directory}")
    print(f"Total number of Word files: {word_file_count}")
    print(f"Total number of existing PDF files: {existing_pdf_count}")

    overwrite_input = input("Do you want to overwrite existing PDF files? (yes/no): ").strip().lower()
    overwrite = overwrite_input == 'yes'

    if overwrite:
        print("WARNING: Existing PDFs will be overwritten. They can't be recovered after this process!")
    else:
        print("No file will be overwritten.")
    
    confirm = input("Do you want to proceed with the conversion? (yes/no): ").strip().lower()
    if confirm == 'yes':
        print("Starting conversion...")
        converted_files, corrupted_files = convert_all_docs_in_directory(directory, overwrite)
        print("Conversion complete.")
        print("\nSUMMARY:")
        print(f"Converted Word files: {word_file_count - corrupted_files}")

        if corrupted_files > 0:
            print(f"Number of files that could not be converted: {corrupted_files}")
        

        if converted_files:
            delete_input = input("Do you want to delete all converted Word files? (yes/no): ").strip().lower()
            if delete_input == 'yes':
                for file in converted_files:
                    os.remove(file)
                    print(f"Deleted: {file}")
                print("All converted Word files have been deleted.")
            else:
                print("No Word files were deleted.")
        else:
            print("No Word files were converted, so no files to delete.")
    else:
        print("Operation cancelled by user.")

if __name__ == "__main__":
    main()
