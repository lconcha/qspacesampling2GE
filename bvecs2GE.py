#!/usr/bin/env python3
import sys
import numpy as np

def bvecs_bvals_to_ge_tensor(bval_file, bvec_file, output_tensor_file, flip_x=True):
    # Load bvals and bvecs
    bvals = np.loadtxt(bval_file)
    bvecs = np.loadtxt(bvec_file)
    
    # Handle shape (bvecs are often 3 x N in FSL format)
    if bvecs.shape[0] == 3 and bvecs.shape[1] != 3:
        bvecs = bvecs.T  # Transpose to N x 3
        
    bvals = np.atleast_1d(bvals)
    bmax = np.max(bvals)
    
    if bmax == 0:
        raise ValueError("Maximum b-value in bvals is 0.")

    ge_vectors = []
    
    for b, vec in zip(bvals, bvecs):
        norm = np.linalg.norm(vec)
        if b == 0 or norm == 0:
            ge_vec = np.array([0.0, 0.0, 0.0])
        else:
            # Normalize vector to unit length
            unit_vec = vec / norm
            # Scale length by sqrt(b / bmax)
            scale = np.sqrt(b / bmax)
            ge_vec = unit_vec * scale
            
            # Flip X coordinate to match GE scanner physical coordinate frame
            if flip_x:
                ge_vec[0] = -ge_vec[0]
                
        ge_vectors.append(ge_vec)

    ge_vectors = np.array(ge_vectors)

    # Write tensor file
    with open(output_tensor_file, 'w') as f:
        # Write number of directions on the first line
        f.write(f"{len(ge_vectors)}\n")
        
        # Write X Y Z components
        for v in ge_vectors:
            f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        f.write(f"6\n")
        for v in range(6):
            f.write(f"0.0 0.0 0.0\n")
            
    print(f"Successfully generated '{output_tensor_file}' with max b-value = {bmax}.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bvecs2GE.py <bvals> <bvecs> <output_tensor.dat>")
        sys.exit(1)
        
    bval_path = sys.argv[1]
    bvec_path = sys.argv[2]
    out_path = sys.argv[3]
    
    bvecs_bvals_to_ge_tensor(bval_path, bvec_path, out_path)