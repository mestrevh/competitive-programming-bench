from pathlib import Path
import pandas as pd

class __FileManager:
    def read_file(self, path: Path) -> str:
        if not path.exists():
            print("[Error]: file is not exist")
        
        try:
            with open(path, "r", encoding="utf-8") as file:
                return file.read()
        except:
            print("[Error]: file can not read")
            return None
    
    def save_file(self, path: Path, content: str) -> bool:
        try:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)
            return True
        except:
            print("[Error]: System dows not save the file")
            return False
            
    
    def save_csv(self, content: pd.DataFrame, path: Path) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            content.to_csv(path, index=False, encoding='utf-8')
            return True
        except:
            print(f"[Error]: System does not save the csv")
            return False
        
    def read_csv(self, path: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(path)
        except:
            print("[Error]: read csv is not completed")
            return None
            
file_manager = __FileManager()