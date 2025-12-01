import argparse
from pipeline import Forma3DPipeline

def main():
    parser = argparse.ArgumentParser(description="Forma3D CLI")
    parser.add_argument("--input", required=True, help="Path to input image")
    parser.add_argument("--output", required=True, help="Path to output model (PLY)")
    
    args = parser.parse_args()
    
    pipeline = Forma3DPipeline()
    pipeline.run(args.input, args.output)

if __name__ == "__main__":
    main()
