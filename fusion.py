import open3d as o3d
import numpy as np
import copy

def preprocess_point_cloud(pcd, voxel_size):
    """
    Downsamples the point cloud, estimates normals, and computes FPFH features.
    """
    pcd_down = pcd.voxel_down_sample(voxel_size)
    
    radius_normal = voxel_size * 2
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))
    
    radius_feature = voxel_size * 5
    pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd_down, pcd_fpfh

def execute_global_registration(source_down, target_down, source_fpfh,
                                target_fpfh, voxel_size):
    """
    Performs RANSAC-based global registration.
    """
    distance_threshold = voxel_size * 1.5
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh, True,
        distance_threshold,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        3, [
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(
                0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(
                distance_threshold)
        ], o3d.pipelines.registration.RANSACConvergenceCriteria(100000, 0.999))
    return result

def refine_registration(source, target, voxel_size, trans_init):
    """
    Refines alignment using Point-to-Plane ICP.
    """
    distance_threshold = voxel_size * 0.4
    
    # Ensure normals are computed for point-to-plane
    if not source.has_normals():
        source.estimate_normals()
    if not target.has_normals():
        target.estimate_normals()
        
    result = o3d.pipelines.registration.registration_icp(
        source, target, distance_threshold, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPlane())
    return result

def fuse_point_clouds(pcds, voxel_size=0.05):
    """
     fuses a list of point clouds into a single one.
     Assumes pcds is a list of open3d.geometry.PointCloud
    """
    if not pcds:
        return None
    if len(pcds) == 1:
        return pcds[0]

    # Target is the accumulated point cloud, starting with the first one
    combined_pcd = pcds[0]
    
    for i in range(1, len(pcds)):
        source = pcds[i]
        target = combined_pcd
        
        # Preprocess
        source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
        target_down, target_fpfh = preprocess_point_cloud(target, voxel_size)
        
        # Global Registration
        result_ransac = execute_global_registration(source_down, target_down,
                                                    source_fpfh, target_fpfh,
                                                    voxel_size)
        
        # Local Refinement
        result_icp = refine_registration(source, target, voxel_size, result_ransac.transformation)
        
        # Transform source and merge
        source.transform(result_icp.transformation)
        combined_pcd += source
        
        # Optional: Downsample combined cloud to keep it manageable
        combined_pcd = combined_pcd.voxel_down_sample(voxel_size=voxel_size/2)

    return combined_pcd
