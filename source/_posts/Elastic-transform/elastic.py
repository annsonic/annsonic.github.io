import numpy as np
import random
import cv2
import matplotlib.pyplot as plt


# Magic numbers
alpha_affine = 112 // 6 # Unit: pixels
sigma = 4 # Unit: pixels
alpha = 34
border_mode = cv2.BORDER_REFLECT_101

# Read the source image
src = cv2.imread('6.png')
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

# Select 3 points (array pts1) for transformation
height, width = src.shape[:2]
center_square = np.float32((height, width)) // 2
square_size = min((height, width)) // 3
pts1 = np.float32(
        [
            center_square + square_size,
            [center_square[0] + square_size, center_square[1] - square_size],
            center_square - square_size,
        ]
    )
# Visualize and save image
src_pts1 = src.copy()
for i,pt in enumerate(pts1):
    cy, cx = int(pt[0]), int(pt[1])
    cv2.circle(src_pts1, (cx,cy), radius=1, color=colors[i], thickness=-1)
cv2.imwrite('pts1.png', src_pts1)

# Perturb 3 points to random positions
random_state = np.random.RandomState(random.randint(0, (1 << 32) - 1))
pts2 = pts1 + random_state.uniform(low=-alpha_affine, high=alpha_affine, size=pts1.shape).astype(
        np.float32)
# Visualize and save image
src_pts2 = src.copy()
for i,pt in enumerate(pts2):
    cy, cx = int(pt[0]), int(pt[1])
    cv2.circle(src_pts2, (cx,cy), radius=1, color=colors[i], thickness=-1)
cv2.imwrite('pts2.png', src_pts2)

# Compute the affine transform matrix
matrix = cv2.getAffineTransform(pts1, pts2)

# Apply transformation
dst_affine = cv2.warpAffine(src_pts2, matrix, (height,width))
# Visualize and save image
cv2.imwrite('affine.png', dst_affine)

# Generate random displacement field in x-direction, range [-1, 1]
dx = random_state.rand(height, width).astype(np.float32) * 2 - 1
# Apply smoothing
cv2.GaussianBlur(dx, (17, 17), sigma, dst=dx, borderType=border_mode)
dx *= alpha
# Duplicate random vector field in y-direction
dy = dx
# Position indices x, y
x, y = np.meshgrid(np.arange(width), np.arange(height))
# Purturbed position indices
map_x = np.float32(x + dx)
map_y = np.float32(y + dy)
# Remap the pixels
dst_mapped = cv2.remap(dst_affine, map_x, map_y, cv2.INTER_LINEAR)

# Visualize the elastic transformation
fig,ax = plt.subplots(1,1)
ax.imshow(dst_mapped)
# Prune the index array to reduce the arrow density
skip=(slice(None,None,4),slice(None,None,4))
ax.quiver(x[skip], y[skip], dx[skip], dy[skip], 
          color='orange', linewidths=(5,), headaxislength=10)
ax.set_axis_off()
plt.savefig('dst.png')
plt.clf()

# Initiate the array as the discrete Dirac delta function
gaussian_kernel = np.zeros((17, 17))
gaussian_kernel[8, 8] = 1
# Apply smoothing
cv2.GaussianBlur(gaussian_kernel, (17, 17), sigma, dst=gaussian_kernel, borderType=border_mode)
gaussian_kernel = gaussian_kernel / gaussian_kernel.sum()
# Visualize the kernel and save image
plt.imshow(gaussian_kernel, cmap=plt.get_cmap('jet'), interpolation='nearest')
plt.colorbar()
plt.savefig('kernel.png')