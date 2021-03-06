import os
import math
import json
import numpy as np
import random
import matplotlib.pyplot as plt
from collections import Counter
from multiprocessing.pool import Pool


SEED = 10
np.random.seed(SEED)
random.seed(SEED)


def eval_func_tuple(f_args):
    return f_args[0](*f_args[1:])

class Clustering:
    def __init__(self, k: int, results_path: str, verbose = False) -> None:
        self.k = k
        self.results_path = results_path
        self.verbose = verbose
    
    def log(self, text) -> None:
        if self.verbose:
            print(text)
    
    @classmethod
    def __get_nearest_cluster(cls, image, clusters):
        distance_to_cluster = math.inf
        cluster_index = 0
        for j, cluster in enumerate(clusters):
            distance = np.square(image - cluster).mean()
            if distance < distance_to_cluster:
                distance_to_cluster = distance
                cluster_index = j
        return (cluster_index, cluster, distance_to_cluster)
    
    @classmethod
    def __get_average_of_cluster_images(cls, cluster_index, images, images_clusters):
        images_indices = [i_i for i_i, c_i in enumerate(images_clusters) if c_i == cluster_index]
        clustered_images = images[images_indices]
        if len(images) == 0:
            images = images[random.randint(0, len(images)-1)]
        else:
            images = np.average(clustered_images, axis=0)
        return images
    
    @classmethod
    def __select_starting_clusters(cls, ds_images: np.ndarray, k: int):
        clusters = ds_images[random.randint(0, len(ds_images)-1)].reshape(1, -1)
        while len(clusters) != k:
            probabilities = []
            for image in ds_images:
                _, _, distance_to_nearest_cluster = cls.__get_nearest_cluster(image, clusters)
                probabilities.append(distance_to_nearest_cluster * distance_to_nearest_cluster)
            p_sum = sum(probabilities)
            probabilities = [p/p_sum for p in probabilities]
            idx = np.random.choice(range(len(ds_images)), p=probabilities)
            clusters = np.append(clusters, [ds_images[idx]], axis=0)
        return clusters

    @classmethod
    def clustering(cls, ds_images: np.ndarray, i: int, n_iter: int, k: int, results_path: str):
        # select k starting clusters
        # clusters = ds_images[random.sample(range(len(ds_images)), k)]
        clusters = cls.__select_starting_clusters(ds_images, k)
        cls.show_centroids(None, 'centroids_start.png', clusters, results_path)
        # look for best configuration
        for j in range(n_iter):
            # divide elements into clusters
            images_clusters = []
            for image in ds_images:
                cluster_index, _, _ = cls.__get_nearest_cluster(image, clusters)
                images_clusters.append(cluster_index)
            # update clusters to be average of its images
            print(f'(clusters {k}, try {i}, iteration {j})')
            for cluster_index, cluster in enumerate(clusters):
                clusters[cluster_index] = cls.__get_average_of_cluster_images(
                    cluster_index, ds_images, images_clusters)
        # choose cluster with overall smallest inertia
        inertia = 0.0
        for image in ds_images:
            distance_to_cluster = math.inf
            for cluster in clusters:
                distance = np.square(image - cluster).mean()
                if distance < distance_to_cluster:
                    distance_to_cluster = distance
            inertia += distance_to_cluster / float(len(clusters))
        return (inertia, clusters)
        
    def train(self, ds_images: np.ndarray, ds_labels: np.ndarray, n_tries: int, n_iter: int) -> None:
        # reshape
        ds_images = ds_images.reshape(len(ds_images), -1)
        # run multiple tries
        with Pool(n_tries) as pool:
            results = pool.map(eval_func_tuple, [(Clustering.clustering, ds_images, i, n_iter, self.k, self.results_path) for i in range(n_tries)])
        self.minimal_inertia = math.inf
        self.best_clusters = None
        for inertia, clusters in results:
            if inertia < self.minimal_inertia:
                self.minimal_inertia = inertia
                self.best_clusters = np.copy(clusters)
        # update labels
        images_clusters = []
        for image in ds_images:
            cluster_index, _, _ = self.__get_nearest_cluster(image, self.best_clusters)
            images_clusters.append(cluster_index)
        self.cluster_labels = []
        for i, cluster in enumerate(self.best_clusters):
            labels = []
            for i_i, c_i in enumerate(images_clusters):
                if i == c_i:
                    labels.append(ds_labels[i_i])
            self.cluster_labels.append(dict(Counter(labels)))

    def save(self):
        with open(os.path.join(self.results_path, 'inertia'), 'w+') as f:
            f.write(f'inertia: {self.minimal_inertia}\n\n')
            f.write(json.dumps(self.cluster_labels, indent=4))
            for line in self.best_clusters:
                f.write(str(list(line)))
    
    def test_accuracy(self, ds_images: np.ndarray = None, ds_labels: np.ndarray = None, filename: str = 'train'):
        accuracy = np.full((self.k, 10), 0.0)
        if ds_images is not None and ds_labels is not None:
            images_clusters = []
            ds_images = ds_images.reshape(len(ds_images), -1)
            for image in ds_images:
                cluster_index, _, _ = self.__get_nearest_cluster(image, self.best_clusters)
                images_clusters.append(cluster_index)
            cluster_labels = []
            for i, cluster in enumerate(self.best_clusters):
                labels = []
                for i_i, c_i in enumerate(images_clusters):
                    if i == c_i:
                        labels.append(ds_labels[i_i])
                cluster_labels.append(dict(Counter(labels)))
        else: cluster_labels = self.cluster_labels
        for i, lab in enumerate(cluster_labels):
            try:
                all_items = sum(lab[key] for key in lab)
                max_label = int(float(max(lab, key=lab.get)))
                for key in lab:
                    accuracy[max_label, 9-int(float(key))] = 100 * float(lab[key]) / all_items if all_items > 0 else 0.0
            except: pass
        with open(os.path.join(self.results_path, f'accuracy - {filename}.txt'), 'w+') as f:
            for row in accuracy:
                f.write(str(row) + '\n')
        plt.figure()
        plt.xticks([i for i in range(10)])
        plt.yticks([i for i in range(self.k)])
        plt.grid(False)
        plt.imshow(accuracy, extent=[-0.5, 9.5, -0.5, self.k - 0.5], vmin=0, vmax=100)
        plt.xlabel('correct labels')
        plt.ylabel('assigned labels')
        plt.colorbar()
        plt.tight_layout()
        plt.savefig(os.path.join(self.results_path, f'accuracy - {filename}.png'))
        plt.clf()
        plt.close()
    
    def show_centroids(self, filename: str, clusters: np.ndarray = None, results_path: str = None):
        if clusters is None: clusters = self.best_clusters
        if results_path is None: results_path = self.results_path
        plt.figure(figsize=(len(clusters), 1))
        for i in range(len(clusters)):
            image = clusters[i]
            s = int(math.sqrt(len(image)))
            image = image.reshape((s, s))
            plt.subplot(1, len(clusters), i+1)
            plt.xticks([])
            plt.yticks([])
            plt.grid(False)
            plt.imshow(image)
        plt.tight_layout()
        plt.savefig(os.path.join(results_path, filename))
        plt.clf()
        plt.close()
